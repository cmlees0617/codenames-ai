import json
from pathlib import Path

import pytest

from clue_eval.boards.io import load_boards_from_json
from clue_eval.paths import default_test_boards_path


def test_load_packaged_fixtures():
    boards = load_boards_from_json(default_test_boards_path())
    assert len(boards) >= 1
    assert "blues" in boards[0]


def test_load_missing_file_returns_empty(tmp_path: Path):
    assert load_boards_from_json(tmp_path / "missing.json") == []


def test_load_invalid_json_raises(tmp_path: Path):
    path = tmp_path / "bad.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON"):
        load_boards_from_json(path)


def test_load_non_array_raises(tmp_path: Path):
    path = tmp_path / "object.json"
    path.write_text(json.dumps({"id": 1}), encoding="utf-8")
    with pytest.raises(ValueError, match="Expected a JSON array"):
        load_boards_from_json(path)
