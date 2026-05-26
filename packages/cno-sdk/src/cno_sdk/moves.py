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


def build_leave_team(
    *,
    player_id: str,
    credentials: str,
) -> dict[str, Any]:
    return build_make_move(
        "leaveTeam",
        [],
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


def build_guess_card(
    word: str,
    *,
    player_id: str,
    credentials: str,
    player_name: str,
    player_team: str,
    player_image: str | None = None,
    card_color: str | None = None,
) -> dict[str, Any]:
    meta: dict[str, Any] = {
        "playerID": player_id,
        "playerName": player_name,
        "playerTeam": player_team,
    }
    if player_image is not None:
        meta["playerImage"] = player_image
    if card_color is not None:
        meta["cardColor"] = card_color
    return build_make_move(
        "guessCard",
        [word.upper(), meta],
        player_id=player_id,
        credentials=credentials,
    )


def build_end_guessing(
    *,
    player_id: str,
    credentials: str,
    player_name: str,
    player_image: str | None = None,
) -> dict[str, Any]:
    player_meta = {"name": player_name, "image": player_image}
    return build_make_move(
        "endGuessing",
        [player_meta],
        player_id=player_id,
        credentials=credentials,
    )


def build_start_match(
    word_entries: list[dict[str, Any]],
    *,
    player_id: str,
    credentials: str,
    player_name: str,
    player_image: str | None = None,
    starting_team: int = 9,
    other_team: int = 8,
    neutral: int = 7,
    assassin: int = 1,
) -> dict[str, Any]:
    return build_make_move(
        "startMatch",
        [
            word_entries,
            {"name": player_name, "image": player_image},
            {
                "startingTeam": starting_team,
                "otherTeam": other_team,
                "neutral": neutral,
                "assasin": assassin,
            },
        ],
        player_id=player_id,
        credentials=credentials,
    )
