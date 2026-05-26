"""Helpers for boardgame.io match roster metadata."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MatchPlayer:
    player_id: str
    name: str | None = None
    is_host: bool = False
    is_connected: bool = False

    @classmethod
    def from_entry(cls, player_id: str, entry: Any) -> MatchPlayer | None:
        if not entry or not isinstance(entry, dict):
            return None
        name = entry.get("name")
        if not name:
            return None
        return cls(
            player_id=str(player_id),
            name=str(name),
            is_host=bool(entry.get("isHost")),
            is_connected=bool(entry.get("isConnected")),
        )


def parse_match_data(raw: Any) -> list[MatchPlayer]:
    """Parse filteredMetadata / matchData payloads into active roster entries."""
    players: list[MatchPlayer] = []
    if isinstance(raw, list):
        for index, entry in enumerate(raw):
            player = MatchPlayer.from_entry(str(index), entry)
            if player is not None:
                players.append(player)
        return players

    if isinstance(raw, dict):
        for player_id, entry in raw.items():
            player = MatchPlayer.from_entry(str(player_id), entry)
            if player is not None:
                players.append(player)
    return players


def player_present(raw: Any, player_id: str) -> bool:
    """Return True if the player still has a named roster entry."""
    if isinstance(raw, list):
        index = int(player_id)
        if index >= len(raw):
            return False
        entry = raw[index]
        return isinstance(entry, dict) and bool(entry.get("name"))
    if isinstance(raw, dict):
        entry = raw.get(player_id) or raw.get(str(player_id))
        return isinstance(entry, dict) and bool(entry.get("name"))
    return False
