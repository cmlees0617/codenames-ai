"""Example demo for the optional embedding-based ClueEngine (not part of clue-eval tests)."""

from __future__ import annotations

from cluegen.algorithms.clue import CluegenClueAlgorithm, default_vocab_path
from game_core.views import SpymasterBoardCard, SpymasterView


def _demo_view() -> SpymasterView:
    """Small hard-coded board so this package does not depend on clue-eval fixtures."""
    cards = (
        SpymasterBoardCard("STREAM", "blue", False),
        SpymasterBoardCard("WASHER", "blue", False),
        SpymasterBoardCard("MINE", "blue", False),
        SpymasterBoardCard("RAINBOW", "red", False),
        SpymasterBoardCard("DISK", "red", False),
        SpymasterBoardCard("WAR", "civilian", False),
        SpymasterBoardCard("ORGAN", "assassin", False),
    )
    return SpymasterView(team="blue", board=cards)


def main() -> None:
    print("Example CluegenClueAlgorithm demo (optional package).")
    print("Benchmark boards: uv run python packages/clue-eval/examples/generate_standard_board_set.py")
    algorithm = CluegenClueAlgorithm(vocab_path=default_vocab_path())
    clues = algorithm.rank_clues(_demo_view(), limit=3)
    for clue in clues:
        print(clue)


if __name__ == "__main__":
    main()
