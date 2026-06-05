"""Load and save evaluation boards as JSON fixtures."""

from __future__ import annotations

import json
from pathlib import Path

from clue_eval.boards.types import FixtureBoard


def mean_board_difficulty(board: FixtureBoard) -> float:
    """Average blue/red difficulty in ``[0, 1]`` (requires ``board['difficulty']``)."""
    difficulty = board["difficulty"]
    return (difficulty["blue"] + difficulty["red"]) / 2.0


def sort_boards_by_difficulty(boards: list[FixtureBoard]) -> list[FixtureBoard]:
    """Return boards sorted easiest-first by mean team difficulty."""
    return sorted(boards, key=mean_board_difficulty)


def save_boards_to_json(
    path: Path,
    boards: list[FixtureBoard],
    *,
    sort_by_difficulty: bool = True,
) -> Path:
    """
    Write boards to a JSON array file.

    When ``sort_by_difficulty`` is true (default), boards are ordered easiest to
    hardest and ``id`` is reassigned to ``1 .. len(boards)`` in that order.
    """
    ordered = sort_boards_by_difficulty(boards) if sort_by_difficulty else list(boards)
    payload: list[FixtureBoard] = []
    for index, board in enumerate(ordered, start=1):
        entry: FixtureBoard = {**board, "id": index}
        payload.append(entry)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def load_boards_from_json(path: Path) -> list[FixtureBoard]:
    """Load all boards from a JSON array file."""
    try:
        with path.open(encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in board fixture: {path}") from exc

    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON array in {path}")
    return data
