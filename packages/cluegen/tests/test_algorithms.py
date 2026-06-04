from cluegen.algorithms.scripted import ScriptedClueAlgorithm, ScriptedGuessAlgorithm
from game_core.types import GuessAction
from game_core.views import (
    BoardTileView,
    ClueHistoryEntry,
    OperativeView,
    SpymasterBoardCard,
    SpymasterView,
)


def test_scripted_clue_algorithm():
    view = SpymasterView(
        team="red",
        board=(
            SpymasterBoardCard("A", "red", False),
            SpymasterBoardCard("B", "blue", False),
        ),
    )
    clues = ScriptedClueAlgorithm().rank_clues(view)
    assert clues[0].intended_targets == ("A",)


def test_scripted_guess_algorithm_queue():
    view = OperativeView(
        team="red",
        board=(BoardTileView("A", False), BoardTileView("B", False)),
        current_clue=ClueHistoryEntry("CLUE", 1),
        guesses_remaining=2,
    )
    algo = ScriptedGuessAlgorithm(["A", None])
    assert algo.guess_word(view) == GuessAction.guess("A")
    assert algo.guess_word(view).pass_turn
