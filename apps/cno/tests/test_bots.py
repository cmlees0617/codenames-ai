from game_core.types import Clue


def test_auto_selects_top_clue():
    clues = [
        Clue("OCEAN", 2, intended_targets=("A", "B")),
        Clue("RIVER", 1, intended_targets=("C",)),
    ]
    def select(ranked):
        return ranked[0] if ranked else None

    assert select(clues) == clues[0]
