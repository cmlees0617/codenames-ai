"""Async Socket.IO client for codenames.game."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Callable
from urllib.parse import urlparse

import socketio

from cno_sdk.credentials import generate_credentials
from cno_sdk.moves import build_give_clue, build_join_team
from cno_sdk.patches import apply_json_patches
from cno_sdk.protocol import build_sync_payload, build_update_payload
from cno_sdk.state import GameState, Role, TeamColor, is_spymaster_turn

logger = logging.getLogger(__name__)

DEFAULT_HOST = "https://server-discord.gke.codenames.game"
DEFAULT_NAMESPACE = "/cno2"
INITIAL_MATCH_ID = "default"
ORIGIN = "https://codenames.game"


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
        room_slug: str,
        nickname: str = "SpymasterBot",
        *,
        host: str = DEFAULT_HOST,
        credentials: str | None = None,
        player_id: str | None = None,
    ) -> None:
        self.room_slug = room_slug
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
        self._last_error: Exception | None = None
        self._redirect_pending = False

        self._register_handlers()

    @property
    def state(self) -> GameState:
        return self._state

    def _register_handlers(self) -> None:
        @self._sio.event(namespace=DEFAULT_NAMESPACE)
        async def connect() -> None:
            logger.info("Connected to %s%s", self.host, self.socket_path)
            self._connected.set()
            if self._redirect_pending:
                return
            if self.match_id != INITIAL_MATCH_ID and self.player_id is not None:
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
            self.match_id = str(match_id)
            if self._state.raw:
                raw = apply_json_patches(self._state.raw, patches)
            else:
                raw = {"G": {}, "ctx": {}, "_stateID": state_id}
                raw = apply_json_patches(raw, patches)
            raw["_stateID"] = state_id
            self._state = GameState.from_bgio(raw)
            self._synced.set()
            self._state_changed.set()
            logger.debug(
                "Applied patch id=%s phase=%s active=%s/%s",
                self._state.state_id,
                self._state.phase,
                self._state.active_team,
                self._state.active_role,
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

        @self._sio.on("room-timeout", namespace=DEFAULT_NAMESPACE)
        async def on_room_timeout(match_id: str) -> None:
            self._last_error = TimeoutError(f"Room timed out: {match_id}")
            logger.error("%s", self._last_error)
            self._synced.set()

    async def _handle_state_event(self, *args: Any) -> None:
        state, metadata = self._parse_state_event(args)
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

        self._state = GameState.from_bgio(state)
        self._synced.set()
        self._state_changed.set()
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
    ) -> tuple[dict[str, Any] | None, dict[str, Any]]:
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
            metadata["matchID"] = match_id
            return payload.get("state") or {}, metadata

        if len(args) >= 1 and isinstance(args[0], dict):
            state = args[0]
            metadata = args[1] if len(args) > 1 and isinstance(args[1], dict) else {}
            return state, metadata

        return None, {}

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

    async def request_sync(self) -> None:
        payload = build_sync_payload(
            match_id=self.match_id,
            player_id=self.player_id,
            credentials=self.credentials,
            room_id=self.room_slug,
            nickname=self.nickname,
        )
        await self._sio.emit("sync", payload, namespace=DEFAULT_NAMESPACE)

    async def _send_move(self, action: dict[str, Any]) -> None:
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
        self._synced.clear()
        await self._sio.emit("update", payload, namespace=DEFAULT_NAMESPACE)
        await asyncio.wait_for(self._synced.wait(), timeout=15)
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

    async def wait_for(
        self,
        predicate: Callable[[GameState], bool],
        *,
        timeout: float = 600,
        poll_interval: float = 1.0,
    ) -> GameState:
        deadline = time.monotonic() + timeout
        next_sync = time.monotonic()
        while time.monotonic() < deadline:
            if predicate(self._state):
                return self._state
            self._state_changed.clear()
            try:
                await asyncio.wait_for(self._state_changed.wait(), timeout=poll_interval)
            except asyncio.TimeoutError:
                if time.monotonic() >= next_sync:
                    await self.request_sync()
                    next_sync = time.monotonic() + 5.0
        raise TimeoutError("Timed out waiting for game state condition")

    async def wait_for_spymaster_turn(
        self,
        team: TeamColor,
        *,
        timeout: float = 600,
    ) -> GameState:
        if self.player_id is None:
            raise RuntimeError("player_id is unknown; connect and sync first")

        return await self.wait_for(
            lambda state: is_spymaster_turn(state, self.player_id, team),
            timeout=timeout,
        )

    async def close(self) -> None:
        if self._sio.connected:
            await self._sio.disconnect()
