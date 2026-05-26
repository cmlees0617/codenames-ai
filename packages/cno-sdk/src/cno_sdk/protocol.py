"""BGIO action builders and wire-format helpers."""

from __future__ import annotations

from typing import Any


def build_make_move(
    move_type: str,
    args: list[Any],
    *,
    player_id: str,
    credentials: str,
) -> dict[str, Any]:
    return {
        "type": "MAKE_MOVE",
        "payload": {
            "type": move_type,
            "args": args,
            "playerID": player_id,
            "credentials": credentials,
        },
    }


def build_sync_payload(
    *,
    match_id: str,
    player_id: str | None,
    credentials: str,
    room_id: str | None,
    nickname: str,
    player_locale: str = "en",
) -> tuple[Any, ...]:
    player_meta: dict[str, Any] = {
        "playerName": nickname,
        "playerImage": None,
        "playerLocale": player_locale,
        "credentials": credentials,
    }
    if room_id:
        player_meta["roomID"] = room_id
    return (match_id, player_id, credentials, player_meta)


def build_update_payload(
    action: dict[str, Any],
    state_id: int,
    match_id: str,
    player_id: str,
) -> tuple[Any, ...]:
    return (action, state_id, match_id, player_id)
