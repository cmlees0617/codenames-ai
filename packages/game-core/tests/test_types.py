import pytest
from game_core.types import Clue, GuessAction


def test_clue_uppercases_word():
    assert Clue("ocean", 2).word == "OCEAN"


def test_guess_action_guess():
    assert GuessAction.guess("tree").word == "TREE"
    assert not GuessAction.guess("tree").pass_turn


def test_guess_action_end_turn():
    assert GuessAction.end_turn().pass_turn
    assert GuessAction.end_turn().word is None


def test_guess_action_invalid():
    with pytest.raises(ValueError):
        GuessAction(word="A", pass_turn=True)
