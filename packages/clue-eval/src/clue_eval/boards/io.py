"""Load evaluation boards from JSON fixtures."""

from __future__ import annotations

import json
from pathlib import Path

from clue_eval.boards.types import FixtureBoard


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
