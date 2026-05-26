"""High-level move builders for codenames.game."""

from __future__ import annotations

from typing import Any

from cno_sdk.protocol import build_make_move


def build_join_team(
    team: str,
    role: str,
    *,
    player_id: str,
    credentials: str,
) -> dict[str, Any]:
    return build_make_move(
        "joinTeam",
        [team, role],
        player_id=player_id,
        credentials=credentials,
    )


def build_give_clue(
    word: str,
    number: str,
    selected_words: list[str],
    *,
    player_id: str,
    credentials: str,
    player_name: str,
    player_image: str | None = None,
) -> dict[str, Any]:
    player_meta = {"name": player_name, "image": player_image}
    return build_make_move(
        "giveClue",
        [{"word": word.upper(), "number": number}, player_meta, selected_words],
        player_id=player_id,
        credentials=credentials,
    )
