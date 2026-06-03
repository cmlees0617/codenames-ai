import json
from pathlib import Path

from cno.views import to_operative_view, to_spymaster_view
from cno_sdk.state import GameState

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


def test_spymaster_view_from_fixture():
    payload = load_fixture("sync_spymaster_turn.json")
    state = GameState.from_bgio(payload["state"])
    view = to_spymaster_view(state, "red")

    unrevealed_red = [
        card.word
        for card in view.board
        if card.color == "red" and not card.revealed
    ]
    assert unrevealed_red == ["PYRAMID", "HEAVEN", "BULB", "CHICK"]


def test_operative_view_hides_unrevealed_colors():
    payload = load_fixture("sync_spymaster_turn.json")
    state = GameState.from_bgio(payload["state"])
    view = to_operative_view(state, "red")

    for tile in view.board:
        if not tile.revealed:
            assert tile.color is None


def test_operative_view_current_clue_when_active():
    payload = load_fixture("sync_spymaster_turn.json")
    state = GameState.from_bgio(payload["state"])
    state.active_team = "red"
    state.guess_limit = 3
    state.log = [
        {
            "action": {
                "payload": {
                    "type": "giveClue",
                    "args": [{"word": "OCEAN", "number": 2}, None, ["HEAVEN", "BULB"]],
                }
            }
        }
    ]
    view = to_operative_view(state, "red")
    assert view.current_clue is not None
    assert view.current_clue.word == "OCEAN"
    assert view.guesses_remaining == 3
