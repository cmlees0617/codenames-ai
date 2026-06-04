import json
from pathlib import Path

from clue_eval.boards.io import (
    load_boards_from_json,
    mean_board_difficulty,
    save_boards_to_json,
    sort_boards_by_difficulty,
)


def _board(bid: int, blue: float, red: float) -> dict:
    return {
        "id": bid,
        "blues": ["A"],
        "reds": ["B"],
        "civilians": ["C"],
        "assassins": ["D"],
        "difficulty": {"blue": blue, "red": red},
    }


def test_sort_boards_by_difficulty():
    boards = [_board(1, 0.8, 0.8), _board(2, 0.1, 0.1), _board(3, 0.5, 0.5)]
    sorted_boards = sort_boards_by_difficulty(boards)
    assert mean_board_difficulty(sorted_boards[0]) == 0.1
    assert mean_board_difficulty(sorted_boards[-1]) == 0.8


def test_save_boards_orders_and_reids(tmp_path: Path):
    boards = [_board(99, 0.9, 0.9), _board(1, 0.2, 0.2)]
    path = tmp_path / "boards.json"
    save_boards_to_json(path, boards)

    loaded = load_boards_from_json(path)
    assert len(loaded) == 2
    assert loaded[0]["id"] == 1
    assert loaded[1]["id"] == 2
    assert mean_board_difficulty(loaded[0]) < mean_board_difficulty(loaded[1])

    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw[0]["id"] == 1
