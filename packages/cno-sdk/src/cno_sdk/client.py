"""Async Socket.IO client for codenames.game."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Callable
from urllib.parse import urlparse

import socketio

from cno_sdk.credentials import generate_credentials
from cno_sdk.match_data import MatchPlayer, parse_match_data, player_present
from cno_sdk.moves import (
    build_end_guessing,
    build_give_clue,
    build_guess_card,
    build_join_team,
    build_leave_team,
    build_start_match,
)
from cno_sdk.patches import apply_json_patches
from cno_sdk.protocol import build_sync_payload, build_update_payload
from cno_sdk.session_log import log_session
from cno_sdk.state import (
    GameState,
    GameView,
    Role,
    TeamColor,
    is_operative_turn,
    is_spymaster_turn,
)
from cno_sdk.words import TEST_BOARD_WORDS, build_word_pack_entries

logger = logging.getLogger(__name__)

DEFAULT_HOST = "https://server-discord.gke.codenames.game"
DEFAULT_NAMESPACE = "/cno2"
INITIAL_MATCH_ID = "default"
ORIGIN = "https://codenames.game"
DEFAULT_MOVE_TIMEOUT = 30.0
LEAVE_MATCH_DELAY = 0.1
REMOVE_PLAYER_TIMEOUT = 5.0


class GameEnded(Exception):
    """Raised when the match ends while waiting for game state."""

    def __init__(self, winner: str | None) -> None:
        self.winner = winner
        super().__init__(f"Game ended: {winner}")


def parse_server_url(server_url: str) -> tuple[str, str]:
    """Split a boardgame.io server URL into host and socket.io path."""
    parsed = urlparse(server_url)
    host = f"{parsed.scheme}://{parsed.netloc}"
    pathname = parsed.path.rstrip("/")
    socket_path = f"{pathname}/socket.io" if pathname else "/socket.io"
    return host, socket_path


class CNOClient:
    """Low-level boardgame.io client for a codenames.game room."""

    def __init__(
        self,
        room_slug: str | None = None,
        nickname: str = "SpymasterBot",
        *,
        host: str = DEFAULT_HOST,
        credentials: str | None = None,
        player_id: str | None = None,
        create_if_missing: bool = False,
        log_session: bool = True,
    ) -> None:
        self._room_slug = room_slug
        self._create_if_missing = create_if_missing or room_slug is None
        self.nickname = nickname
        self.host = host.rstrip("/")
        self.socket_path = "/socket.io"
        self.credentials = credentials or generate_credentials()
        self.player_id = player_id
        self.match_id = INITIAL_MATCH_ID

        self._sio = socketio.AsyncClient(
            reconnection=True,
            reconnection_attempts=5,
            logger=False,
            engineio_logger=False,
        )
        self._state = GameState.from_bgio({"G": {}, "ctx": {}, "_stateID": 0})
        self._connected = asyncio.Event()
        self._synced = asyncio.Event()
        self._state_changed = asyncio.Event()
        self._move_done = asyncio.Event()
        self._last_error: Exception | None = None
        self._redirect_pending = False
        self._closing = False
        self._match_data_raw: Any = None
        self._match_players: list[MatchPlayer] = []
        self._match_data_changed = asyncio.Event()
        self._log_session = log_session
        self._pending_patches: dict[int, tuple[int, list[dict[str, Any]]]] = {}
        self._awaiting_match_start = False

        self._register_handlers()

    @property
    def room_slug(self) -> str:
        if not self._room_slug:
            raise RuntimeError("room slug is not assigned yet")
        return self._room_slug

    @property
    def state(self) -> GameState:
        return self._state

    @property
    def match_players(self) -> list[MatchPlayer]:
        return list(self._match_players)

    def get_game_state(self) -> GameView:
        """Return a structured snapshot of the current board, clues, and guesses."""
        return self._state.to_view()

    @classmethod
    async def create_room(
        cls,
        nickname: str = "TestHost",
        *,
        credentials: str | None = None,
    ) -> CNOClient:
        """Connect to the lobby and create a brand-new room."""
        client = cls(
            room_slug=None,
            nickname=nickname,
            credentials=credentials,
            create_if_missing=True,
        )
        await client.connect()
        return client

    @classmethod
    async def resume(
        cls,
        *,
        room_slug: str,
        match_id: str,
        player_id: str,
        credentials: str,
        nickname: str = "Bot",
        host: str = DEFAULT_HOST,
        socket_path: str = "/socket.io",
        log_session: bool = False,
    ) -> CNOClient:
        """Reconnect to an existing player slot using saved session tokens."""
        client = cls(
            room_slug=room_slug,
            nickname=nickname,
            credentials=credentials,
            player_id=str(player_id),
            host=host,
            log_session=log_session,
        )
        client.match_id = match_id
        client.socket_path = socket_path
        await client.connect()
        return client

    def _update_match_data(self, raw: Any) -> None:
        self._match_data_raw = raw
        self._match_players = parse_match_data(raw)
        self._match_data_changed.set()

    def _apply_patch(self, state_id: int, patches: list[dict[str, Any]]) -> None:
        try:
            if self._state.raw:
                raw = apply_json_patches(self._state.raw, patches)
            else:
                raw = {"G": {}, "ctx": {}, "_stateID": state_id}
                raw = apply_json_patches(raw, patches)
        except Exception as exc:
            logger.warning("Failed to apply patch, requesting sync: %s", exc)
            self._pending_patches.clear()
            self._move_done.set()
            raise
        raw["_stateID"] = state_id
        self._state = GameState.from_bgio(raw, log=self._state.log)
        self._synced.set()
        self._state_changed.set()
        self._move_done.set()
        logger.debug(
            "Applied patch id=%s phase=%s active=%s/%s",
            self._state.state_id,
            self._state.phase,
            self._state.active_team,
            self._state.active_role,
        )

    def _drain_pending_patches(self) -> None:
        while True:
            next_id = self._state.state_id + 1
            pending = self._pending_patches.get(next_id)
            if pending is None:
                return
            prev_state_id, patches = pending
            if prev_state_id != self._state.state_id:
                return
            del self._pending_patches[next_id]
            self._apply_patch(next_id, patches)

    async def _on_patch(
        self,
        match_id: str,
        prev_state_id: int,
        state_id: int,
        patches: list[dict[str, Any]],
    ) -> None:
        self.match_id = str(match_id)
        local_id = self._state.state_id
        if state_id <= local_id:
            logger.debug(
                "Ignoring stale patch id=%s (local=%s prev=%s)",
                state_id,
                local_id,
                prev_state_id,
            )
            return
        if prev_state_id < local_id:
            logger.debug(
                "Ignoring replayed patch id=%s (local=%s prev=%s)",
                state_id,
                local_id,
                prev_state_id,
            )
            return
        if prev_state_id != local_id:
            self._pending_patches[state_id] = (prev_state_id, patches)
            logger.debug(
                "Buffered out-of-order patch id=%s (local=%s prev=%s)",
                state_id,
                local_id,
                prev_state_id,
            )
            if not self._awaiting_match_start:
                self._move_done.set()
                await self.request_sync()
            return
        try:
            self._apply_patch(state_id, patches)
        except Exception:
            await self.request_sync()
            return
        self._drain_pending_patches()

    def _register_handlers(self) -> None:
        @self._sio.event(namespace=DEFAULT_NAMESPACE)
        async def connect() -> None:
            logger.info("Connected to %s%s", self.host, self.socket_path)
            self._connected.set()
            if self._redirect_pending:
                return
            await self.request_sync()

        @self._sio.event(namespace=DEFAULT_NAMESPACE)
        async def disconnect() -> None:
            logger.info("Disconnected from server")
            self._connected.clear()
            self._synced.clear()

        @self._sio.on("sync", namespace=DEFAULT_NAMESPACE)
        async def on_sync(*args: Any) -> None:
            await self._handle_state_event(*args)

        @self._sio.on("update", namespace=DEFAULT_NAMESPACE)
        async def on_update(*args: Any) -> None:
            await self._handle_state_event(*args)

        @self._sio.on("patch", namespace=DEFAULT_NAMESPACE)
        async def on_patch(
            match_id: str,
            prev_state_id: int,
            state_id: int,
            patches: list[dict[str, Any]],
            *_args: Any,
        ) -> None:
            await self._on_patch(match_id, prev_state_id, state_id, patches)

        @self._sio.on("matchData", namespace=DEFAULT_NAMESPACE)
        async def on_match_data(match_id: str, data: Any, _user_count: Any = None) -> None:
            if str(match_id) != self.match_id:
                return
            self._update_match_data(data)
            logger.debug(
                "Match roster updated (%d players): %s",
                len(self._match_players),
                ", ".join(f"{p.name or p.player_id}" for p in self._match_players),
            )

        @self._sio.on("updateServerURL", namespace=DEFAULT_NAMESPACE)
        async def on_update_server_url(server_url: str) -> None:
            await self._reconnect_to(server_url)

        @self._sio.on("createdMatch", namespace=DEFAULT_NAMESPACE)
        async def on_created_match(
            room_id: str,
            match_id: str,
            player_id: str,
            creds: str,
            server_url: str | None = None,
        ) -> None:
            self._room_slug = room_id
            self.match_id = match_id
            self.player_id = str(player_id)
            if creds:
                self.credentials = creds
            logger.info(
                "Created/joined match %s as player %s (room=%s)",
                match_id,
                player_id,
                room_id,
            )
            if server_url:
                host, socket_path = parse_server_url(server_url)
                if host != self.host or socket_path != self.socket_path:
                    await self._reconnect_to(server_url)
                    return
            await self.request_sync()

        @self._sio.on("joinedMatch", namespace=DEFAULT_NAMESPACE)
        async def on_joined_match(match_id: str, player_id: str, creds: str) -> None:
            self.match_id = match_id
            self.player_id = str(player_id)
            if creds:
                self.credentials = creds
            logger.info("Joined match %s as player %s", match_id, player_id)

        @self._sio.on("sync-error", namespace=DEFAULT_NAMESPACE)
        async def on_sync_error(payload: dict[str, Any]) -> None:
            error = payload.get("error", payload)
            match_id = payload.get("matchID", self.match_id)
            self._last_error = RuntimeError(f"sync-error for {match_id}: {error}")
            logger.error("%s", self._last_error)
            self._synced.set()
            self._move_done.set()

        @self._sio.on("room-timeout", namespace=DEFAULT_NAMESPACE)
        async def on_room_timeout(match_id: str) -> None:
            self._last_error = TimeoutError(f"Room timed out: {match_id}")
            logger.error("%s", self._last_error)
            self._synced.set()
            self._move_done.set()

    async def _handle_state_event(self, *args: Any) -> None:
        state, metadata, log = self._parse_state_event(args)
        if state is None:
            logger.debug("Ignoring state event with args=%r", args)
            return

        server_url = metadata.get("serverURL")
        if server_url:
            host, socket_path = parse_server_url(server_url)
            if host != self.host or socket_path != self.socket_path:
                await self._reconnect_to(server_url)
                return

        if metadata.get("playerID") is not None:
            self.player_id = str(metadata["playerID"])
        if metadata.get("matchID") is not None:
            self.match_id = str(metadata["matchID"])

        filtered = metadata.get("filteredMetadata")
        if filtered is not None:
            self._update_match_data(filtered)

        self._state = GameState.from_bgio(state, log=log)
        self._pending_patches.clear()
        self._synced.set()
        self._state_changed.set()
        self._move_done.set()
        logger.debug(
            "State updated id=%s phase=%s active=%s/%s",
            self._state.state_id,
            self._state.phase,
            self._state.active_team,
            self._state.active_role,
        )

    @staticmethod
    def _parse_state_event(
        args: tuple[Any, ...],
    ) -> tuple[dict[str, Any] | None, dict[str, Any], list[dict[str, Any]]]:
        if (
            len(args) == 2
            and isinstance(args[0], str)
            and isinstance(args[1], dict)
        ):
            match_id, payload = args
            metadata = {key: value for key, value in payload.items() if key != "state"}
            filtered = payload.get("filteredMetadata")
            if isinstance(filtered, dict) and filtered.get("playerID") is not None:
                metadata["playerID"] = filtered["playerID"]
            if filtered is not None:
                metadata["filteredMetadata"] = filtered
            metadata["matchID"] = match_id
            log = payload.get("log") or []
            return payload.get("state") or {}, metadata, list(log)

        if len(args) >= 1 and isinstance(args[0], dict):
            state = args[0]
            metadata = args[1] if len(args) > 1 and isinstance(args[1], dict) else {}
            return state, metadata, []

        return None, {}, []

    async def _reconnect_to(self, server_url: str) -> None:
        host, socket_path = parse_server_url(server_url)
        if host == self.host and socket_path == self.socket_path:
            return
        logger.info("Redirecting to %s%s", host, socket_path)
        self.host = host
        self.socket_path = socket_path
        self._redirect_pending = True
        if self._sio.connected:
            await self._sio.disconnect()
        await self._connect_to_current_host()
        self._redirect_pending = False
        await self.request_sync()

    async def _connect_to_current_host(self) -> None:
        self._connected.clear()
        self._synced.clear()
        await self._sio.connect(
            self.host,
            namespaces=[DEFAULT_NAMESPACE],
            socketio_path=self.socket_path,
            transports=["websocket"],
            headers={"Origin": ORIGIN},
            wait_timeout=20,
        )
        await asyncio.wait_for(self._connected.wait(), timeout=20)

    async def connect(self) -> None:
        """Connect to the room and perform the initial sync."""
        await self._connect_to_current_host()
        await asyncio.wait_for(self._synced.wait(), timeout=30)
        if self._last_error:
            raise self._last_error
        if self._create_if_missing and not self._room_slug:
            raise RuntimeError("Room creation failed: no room slug assigned")
        if self._log_session and self.player_id is not None and self._room_slug:
            log_session(self)

    @staticmethod
    def _match_started(state: GameState) -> bool:
        return (
            state.cards_dealed
            and state.active_team is not None
            and state.active_role is not None
            and len(state.grid) > 0
        )

    async def _ensure_synced(self, *, timeout: float = 10.0) -> None:
        """Request a full state snapshot and wait for it to arrive."""
        self._synced.clear()
        await self.request_sync()
        await asyncio.wait_for(self._synced.wait(), timeout=timeout)

    async def _wait_for_state(
        self,
        predicate: Callable[[GameState], bool],
        *,
        timeout: float,
        poll_interval: float = 0.25,
        timeout_message: str = "Timed out waiting for game state condition",
    ) -> GameState:
        """Wait for a state predicate without losing patch wakeups."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if predicate(self._state):
                return self._state
            self._state_changed.clear()
            if predicate(self._state):
                return self._state
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            try:
                await asyncio.wait_for(
                    self._state_changed.wait(),
                    timeout=min(poll_interval, remaining),
                )
            except asyncio.TimeoutError:
                continue
        raise TimeoutError(timeout_message)

    async def request_sync(self) -> None:
        room_id = None if self._create_if_missing and not self._room_slug else self._room_slug
        payload = build_sync_payload(
            match_id=self.match_id,
            player_id=self.player_id,
            credentials=self.credentials,
            room_id=room_id,
            nickname=self.nickname,
        )
        await self._sio.emit("sync", payload, namespace=DEFAULT_NAMESPACE)

    async def _send_move(
        self,
        action: dict[str, Any],
        *,
        timeout: float = DEFAULT_MOVE_TIMEOUT,
    ) -> None:
        if self.player_id is None:
            await self.request_sync()
            await asyncio.wait_for(self._synced.wait(), timeout=10)
            if self.player_id is None:
                raise RuntimeError("No playerID assigned after sync")

        payload = build_update_payload(
            action,
            self._state.state_id,
            self.match_id,
            self.player_id,
        )
        self._last_error = None
        self._move_done.clear()
        await self._sio.emit("update", payload, namespace=DEFAULT_NAMESPACE)
        await asyncio.wait_for(self._move_done.wait(), timeout=timeout)
        if self._last_error:
            raise self._last_error

    async def join_team(self, team: TeamColor, role: Role) -> None:
        action = build_join_team(
            team,
            role,
            player_id=self.player_id or "0",
            credentials=self.credentials,
        )
        await self._send_move(action)

    async def leave_team(self) -> None:
        """Leave the current team without disconnecting from the room."""
        if self.player_id is None:
            return
        action = build_leave_team(
            player_id=self.player_id,
            credentials=self.credentials,
        )
        await self._send_move(action, timeout=10.0)

    async def remove_player(self) -> None:
        """Remove this client from the match roster."""
        if not self._sio.connected or self.player_id is None:
            return

        self._match_data_changed.clear()
        await self._sio.emit(
            "removePlayer",
            (self.match_id, self.player_id, self.credentials, self.player_id),
            namespace=DEFAULT_NAMESPACE,
        )
        await self._wait_for_player_removed()

    async def _wait_for_player_removed(self) -> None:
        if self.player_id is None:
            return
        if not player_present(self._match_data_raw, self.player_id):
            return

        deadline = time.monotonic() + REMOVE_PLAYER_TIMEOUT
        while time.monotonic() < deadline:
            if not player_present(self._match_data_raw, self.player_id):
                return
            self._match_data_changed.clear()
            try:
                await asyncio.wait_for(
                    self._match_data_changed.wait(),
                    timeout=max(0.1, deadline - time.monotonic()),
                )
            except asyncio.TimeoutError:
                await self.request_sync()
        logger.warning(
            "Timed out waiting for player %s to leave match %s",
            self.player_id,
            self.match_id,
        )

    async def leave(self) -> None:
        """Leave team, remove player from match, and disconnect."""
        if self._closing:
            return
        self._closing = True
        try:
            if self._sio.connected and self.player_id is not None:
                try:
                    await self.leave_team()
                except Exception as exc:
                    logger.debug("leaveTeam during cleanup failed: %s", exc)
                await asyncio.sleep(LEAVE_MATCH_DELAY)
                try:
                    await self.remove_player()
                except Exception as exc:
                    logger.debug("removePlayer during cleanup failed: %s", exc)
        finally:
            if self._sio.connected:
                await self._sio.disconnect()

    async def start_match(
        self,
        words: tuple[str, ...] | list[str] | None = None,
    ) -> None:
        """Deal cards and begin the match (host action)."""
        await self._ensure_synced()
        word_entries = build_word_pack_entries(words or TEST_BOARD_WORDS)
        action = build_start_match(
            word_entries,
            player_id=self.player_id or "0",
            credentials=self.credentials,
            player_name=self.nickname,
        )
        self._awaiting_match_start = True
        try:
            for attempt in range(2):
                try:
                    await self._send_move(action, timeout=30.0)
                    break
                except asyncio.TimeoutError:
                    if attempt == 0:
                        logger.warning("startMatch move timed out; resyncing and retrying")
                        await self._ensure_synced()
                    else:
                        raise
            try:
                await self._wait_for_state(
                    self._match_started,
                    timeout=5.0,
                    timeout_message="Timed out waiting for match to start",
                )
                return
            except TimeoutError:
                pass
            if not self._match_started(self._state):
                self._awaiting_match_start = False
                self._pending_patches.clear()
                await self._ensure_synced()
                if self._match_started(self._state):
                    return
                self._awaiting_match_start = True
            await self._wait_for_state(
                self._match_started,
                timeout=55.0,
                timeout_message="Timed out waiting for match to start",
            )
        finally:
            self._awaiting_match_start = False
            self._pending_patches.clear()

    async def give_clue(
        self,
        word: str,
        selected_words: list[str],
    ) -> None:
        number = str(len(selected_words))
        action = build_give_clue(
            word,
            number,
            [w.upper() for w in selected_words],
            player_id=self.player_id or "0",
            credentials=self.credentials,
            player_name=self.nickname,
        )
        await self._send_move(action)

    async def guess_card(self, word: str) -> None:
        if self.player_id is None or self._state.active_team is None:
            raise RuntimeError("Cannot guess before sync assigns player and team")
        action = build_guess_card(
            word,
            player_id=self.player_id,
            credentials=self.credentials,
            player_name=self.nickname,
            player_team=self._state.active_team,
        )
        await self._send_move(action)

    async def end_guessing(self) -> None:
        action = build_end_guessing(
            player_id=self.player_id or "0",
            credentials=self.credentials,
            player_name=self.nickname,
        )
        await self._send_move(action)

    async def wait_for(
        self,
        predicate: Callable[[GameState], bool],
        *,
        timeout: float | None = None,
        poll_interval: float = 1.0,
        leave_on_game_end: bool = True,
        shutdown: asyncio.Event | None = None,
    ) -> GameState:
        deadline = None if timeout is None else time.monotonic() + timeout
        next_sync = time.monotonic()
        while deadline is None or time.monotonic() < deadline:
            if shutdown is not None and shutdown.is_set():
                raise asyncio.CancelledError("Shutdown requested")
            if self._state.gameover is not None:
                if leave_on_game_end:
                    await self.leave()
                    raise GameEnded(self._state.gameover)
                return self._state
            if predicate(self._state):
                return self._state
            self._state_changed.clear()
            if predicate(self._state):
                return self._state
            try:
                wait_timeout = poll_interval
                if shutdown is not None:
                    wait_timeout = min(poll_interval, 0.25)
                await asyncio.wait_for(self._state_changed.wait(), timeout=wait_timeout)
            except asyncio.TimeoutError:
                if shutdown is not None and shutdown.is_set():
                    raise asyncio.CancelledError("Shutdown requested")
                if time.monotonic() >= next_sync:
                    await self.request_sync()
                    next_sync = time.monotonic() + 5.0
                continue
            if predicate(self._state):
                return self._state
        raise TimeoutError("Timed out waiting for game state condition")

    async def wait_for_game_over(self, *, timeout: float | None = None) -> GameState:
        """Wait for the match to finish without leaving the room."""
        state = await self.wait_for(
            lambda game_state: game_state.gameover is not None,
            timeout=timeout,
            leave_on_game_end=False,
        )
        logger.info("Game over: %s", state.gameover)
        return state

    async def wait_for_spymaster_turn(
        self,
        team: TeamColor,
        *,
        timeout: float | None = None,
        shutdown: asyncio.Event | None = None,
        leave_on_game_end: bool = False,
    ) -> GameState:
        if self.player_id is None:
            raise RuntimeError("player_id is unknown; connect and sync first")

        return await self.wait_for(
            lambda state: is_spymaster_turn(state, self.player_id, team),
            timeout=timeout,
            shutdown=shutdown,
            leave_on_game_end=leave_on_game_end,
        )

    async def wait_for_operative_turn(
        self,
        team: TeamColor,
        *,
        timeout: float | None = None,
        shutdown: asyncio.Event | None = None,
        leave_on_game_end: bool = False,
    ) -> GameState:
        if self.player_id is None:
            raise RuntimeError("player_id is unknown; connect and sync first")

        return await self.wait_for(
            lambda state: is_operative_turn(state, self.player_id, team),
            timeout=timeout,
            shutdown=shutdown,
            leave_on_game_end=leave_on_game_end,
        )

    async def close(self) -> None:
        await self.leave()
