"""Pure decision-making protocols (no I/O)."""

from __future__ import annotations

from typing import Protocol

from game_core.types import Clue, GuessAction
from game_core.views import OperativeView, SpymasterView


class ClueAlgorithm(Protocol):
    def rank_clues(self, state: SpymasterView, *, limit: int = 10) -> list[Clue]:
        """Return candidate clues best-first."""


class GuessAlgorithm(Protocol):
    def guess_word(self, state: OperativeView) -> GuessAction:
        """Return the next guess or elect to pass."""
