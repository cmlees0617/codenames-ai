"""Minimal ClueAlgorithm for smoke tests without ML dependencies."""

from __future__ import annotations

from game_core.types import Clue
from game_core.views import SpymasterView


class StubClueAlgorithm:
    """Return a deterministic TEST clue from the first friendly targets on the board."""

    def rank_clues(self, state: SpymasterView, *, limit: int = 10) -> list[Clue]:
        targets = tuple(
            card.word
            for card in state.board
            if not card.revealed and card.color == state.team
        )[:3]
        if not targets:
            return []
        clue = Clue(word="TEST", count=len(targets), intended_targets=targets)
        return [clue][:limit]
