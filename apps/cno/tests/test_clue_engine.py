import json
from pathlib import Path

import pytest

from cno.views import to_spymaster_view
from cno_sdk.state import GameState
from cluegen.algorithms import CluegenClueAlgorithm

FIXTURES = (
    Path(__file__).resolve().parents[3]
    / "packages"
    / "cno-sdk"
    / "tests"
    / "fixtures"
)


def load_fixture(name: str) -> dict:
    with open(FIXTURES / name, encoding="utf-8") as handle:
        return json.load(handle)


@pytest.mark.integration
def test_cluegen_algorithm_generates_clue_for_fixture_board():
    payload = load_fixture("sync_spymaster_turn.json")
    state = GameState.from_bgio(payload["state"])
    view = to_spymaster_view(state, "red")
    clues = CluegenClueAlgorithm().rank_clues(view, limit=3)

    assert clues
    clue = clues[0]
    assert clue.word
    assert 1 <= clue.count <= 3
    assert all(target in {"PYRAMID", "HEAVEN", "BULB", "CHICK"} for target in clue.intended_targets)
