from cluegen.algorithms import (
    RandomGuessAlgorithm,
    ScriptedClueAlgorithm,
    ScriptedGuessAlgorithm,
)
from game_core.algorithms import ClueAlgorithm, GuessAlgorithm
from game_core.views import SpymasterBoardCard, SpymasterView


def test_clue_algorithms_satisfy_protocol() -> None:
    view = SpymasterView(
        team="red",
        board=(SpymasterBoardCard("A", "red", False),),
    )
    algo = ScriptedClueAlgorithm()
    assert isinstance(algo, ClueAlgorithm)
    assert algo.rank_clues(view, limit=1)


def test_guess_algorithms_satisfy_protocol() -> None:
    for algo in (ScriptedGuessAlgorithm(), RandomGuessAlgorithm()):
        assert isinstance(algo, GuessAlgorithm)
