"""Pure decision-making protocols (no I/O)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from game_core.types import Clue, GuessAction
from game_core.views import OperativeView, SpymasterView


@runtime_checkable
class ClueAlgorithm(Protocol):
    def rank_clues(self, state: SpymasterView, *, limit: int = 10) -> list[Clue]:
        """Return candidate clues best-first."""


@runtime_checkable
class GuessAlgorithm(Protocol):
    def guess_word(self, state: OperativeView) -> GuessAction:
        """Return the next guess or elect to pass."""
