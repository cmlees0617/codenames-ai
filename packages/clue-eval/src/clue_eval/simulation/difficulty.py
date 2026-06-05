"""Attach board difficulty metadata to simulation results."""

from __future__ import annotations

from game_core.types import TeamColor

from clue_eval.boards.io import mean_board_difficulty
from clue_eval.boards.types import FixtureBoard


def difficulty_fields_for_board(
    board: FixtureBoard,
    test_team: TeamColor,
) -> dict[str, float | None]:
    """
    Extract difficulty scores for correlating outcomes with board hardness.

    Returns ``None`` values when the fixture has no ``difficulty`` block.
    """
    raw = board.get("difficulty")
    if raw is None:
        return {
            "difficulty_blue": None,
            "difficulty_red": None,
            "difficulty_mean": None,
            "difficulty_test_team": None,
        }

    blue = float(raw["blue"])
    red = float(raw["red"])
    return {
        "difficulty_blue": blue,
        "difficulty_red": red,
        "difficulty_mean": mean_board_difficulty(board),
        "difficulty_test_team": blue if test_team == "blue" else red,
    }


