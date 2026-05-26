import pytest

from cno_sdk.state import GameState, is_operative_turn, is_seated


def _state(**overrides) -> GameState:
    raw = {
        "G": {
            "activeTeam": "red",
            "activeRole": "operatives",
            "cardsDealed": True,
            "gameover": None,
            "guessLimit": 3,
            "grid": [],
            "teams": {
                "red": {"operatives": {"p#1": True}, "spymasters": {}},
                "blue": {"operatives": {}, "spymasters": {}},
            },
        },
        "ctx": {"phase": "game"},
        "_stateID": 1,
    }
    return GameState.from_bgio(raw)


def test_is_operative_turn():
    state = _state()
    assert is_operative_turn(state, "1", "red") is True
    assert is_operative_turn(state, "2", "red") is False


def test_is_operative_turn_requires_guess_limit():
    state = _state()
    state = GameState.from_bgio(
        {
            **state.raw,
            "G": {**state.raw["G"], "guessLimit": 0},
        }
    )
    assert is_operative_turn(state, "1", "red") is False
