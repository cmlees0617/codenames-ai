import json
from pathlib import Path

from cno_sdk.state import (
    GameState,
    parse_clues,
    parse_guesses,
)


FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str):
    return json.loads((FIXTURES / name).read_text())


def test_parse_clues_from_log():
    log = load_fixture("game_log.json")
    clues = parse_clues(log)
    assert len(clues) == 1
    assert clues[0].word == "PINEAPPLE"
    assert clues[0].count == 3
    assert clues[0].selected_words == ["HEAVEN", "BULB", "CHICK"]


def test_parse_guesses_from_log():
    log = load_fixture("game_log.json")
    guesses = parse_guesses(log)
    assert len(guesses) == 2
    assert guesses[0].word == "HEAVEN"
    assert guesses[0].card_color == "red"
    assert guesses[0].team == "red"
    assert guesses[1].word == "MOUNT"
    assert guesses[1].card_color == "civilian"


def test_game_view_from_fixture_state():
    fixture = load_fixture("sync_spymaster_turn.json")
    log = load_fixture("game_log.json")
    state = GameState.from_bgio(fixture["state"], log=log)
    view = state.to_view()
    assert len(view.board) == 6
    assert view.board[2].word == "HEAVEN"
    assert view.board[2].color == "red"
    assert view.board[2].revealed is False
    assert view.board[5].color == "assassin"
    assert len(view.clues) == 1
    assert len(view.guesses) == 2
