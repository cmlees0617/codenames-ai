"""Persist codenames.game session tokens for reconnect and cleanup."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from cno_sdk.client import CNOClient

logger = logging.getLogger(__name__)

DEFAULT_SESSION_LOG = Path.home() / ".codenames-ai" / "sessions.jsonl"


@dataclass(frozen=True)
class PlayerSession:
    room: str
    match_id: str
    player_id: str
    credentials: str
    nickname: str
    host: str
    socket_path: str
    logged_at: str

    @classmethod
    def from_client(cls, client: CNOClient) -> PlayerSession:
        return cls(
            room=client.room_slug,
            match_id=client.match_id,
            player_id=str(client.player_id),
            credentials=client.credentials,
            nickname=client.nickname,
            host=client.host,
            socket_path=client.socket_path,
            logged_at=datetime.now(timezone.utc).isoformat(),
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PlayerSession:
        return cls(
            room=str(data["room"]),
            match_id=str(data["match_id"]),
            player_id=str(data["player_id"]),
            credentials=str(data["credentials"]),
            nickname=str(data.get("nickname", "Bot")),
            host=str(data.get("host", "https://server-discord.gke.codenames.game")),
            socket_path=str(data.get("socket_path", "/socket.io")),
            logged_at=str(data.get("logged_at", "")),
        )


def session_log_path(path: Path | None = None) -> Path:
    return path or DEFAULT_SESSION_LOG


def log_session(
    client: CNOClient,
    *,
    path: Path | None = None,
) -> PlayerSession:
    """Append a session record so the player can be reconnected later."""
    if client.player_id is None or not client._room_slug:
        raise RuntimeError("Cannot log session before player_id and room are assigned")

    record = PlayerSession.from_client(client)
    log_file = session_log_path(path)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with log_file.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(record)) + "\n")

    logger.info(
        "Logged session room=%s player_id=%s credentials=%s (file=%s)",
        record.room,
        record.player_id,
        record.credentials,
        log_file,
    )
    return record


def load_sessions(
    *,
    path: Path | None = None,
    room: str | None = None,
) -> list[PlayerSession]:
    log_file = session_log_path(path)
    if not log_file.exists():
        return []

    sessions: list[PlayerSession] = []
    for line in log_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        record = PlayerSession.from_dict(json.loads(line))
        if room is None or record.room == room:
            sessions.append(record)
    return sessions


async def cleanup_logged_sessions(
    *,
    room: str | None = None,
    path: Path | None = None,
) -> list[str]:
    """Reconnect to logged sessions and leave the match."""
    from cno_sdk.client import CNOClient

    cleaned: list[str] = []
    seen: set[tuple[str, str]] = set()
    for session in load_sessions(path=path, room=room):
        key = (session.room, session.player_id)
        if key in seen:
            continue
        seen.add(key)
        try:
            client = await CNOClient.resume(
                room_slug=session.room,
                match_id=session.match_id,
                player_id=session.player_id,
                credentials=session.credentials,
                nickname=session.nickname,
                host=session.host,
                socket_path=session.socket_path,
            )
            client._log_session = False
            await client.leave()
            cleaned.append(f"{session.room}#{session.player_id}")
        except Exception as exc:
            logger.warning(
                "Failed to cleanup logged session %s#%s: %s",
                session.room,
                session.player_id,
                exc,
            )
    return cleaned


def latest_session(
    *,
    path: Path | None = None,
    room: str | None = None,
    player_id: str | None = None,
) -> PlayerSession | None:
    matches = load_sessions(path=path, room=room)
    if player_id is not None:
        matches = [s for s in matches if s.player_id == player_id]
    return matches[-1] if matches else None
