import json
from pathlib import Path

import pytest

from cno.clue_engine import BoardCategories, board_categories, enemy_team
from cno_sdk.state import GameState


FIXTURES = Path(__file__).resolve().parents[2] / "cno-sdk" / "tests" / "fixtures"


def load_fixture(name: str) -> dict:
    with open(FIXTURES / name, encoding="utf-8") as handle:
        return json.load(handle)


def test_enemy_team():
    assert enemy_team("red") == "blue"
    assert enemy_team("blue") == "red"


def test_board_categories_from_fixture():
    payload = load_fixture("sync_spymaster_turn.json")
    state = GameState.from_bgio(payload["state"])

    red = board_categories(state, "red")
    assert red == BoardCategories(
        targets=["PYRAMID", "HEAVEN", "BULB", "CHICK"],
        civilians=[],
        enemies=["RULER"],
        assassins=["CROSS"],
    )

    blue = board_categories(state, "blue")
    assert blue == BoardCategories(
        targets=["RULER"],
        civilians=[],
        enemies=["PYRAMID", "HEAVEN", "BULB", "CHICK"],
        assassins=["CROSS"],
    )


def test_board_categories_ignores_revealed_cards():
    payload = load_fixture("sync_spymaster_turn.json")
    state = GameState.from_bgio(payload["state"])
    state.grid[1].revealed = True

    red = board_categories(state, "red")
    assert red.targets == ["HEAVEN", "BULB", "CHICK"]


@pytest.mark.integration
def test_clue_engine_generates_clue_for_fixture_board():
    from cno.clue_engine import ClueEngine

    payload = load_fixture("sync_spymaster_turn.json")
    state = GameState.from_bgio(payload["state"])
    clue = ClueEngine().generate(state, "red")

    assert clue.word
    assert 1 <= len(clue.targets) <= 3
    assert all(target in {"PYRAMID", "HEAVEN", "BULB", "CHICK"} for target in clue.targets)
