"""Pure decision-making protocols (no I/O).

Implement these in ``cluegen`` or test doubles; player bots call them from
sync context (often via ``asyncio.to_thread``).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from game_core.types import Clue, GuessAction
from game_core.views import OperativeView, SpymasterView


@runtime_checkable
class ClueAlgorithm(Protocol):
    """Rank candidate clues for a spymaster turn (best first)."""

    def rank_clues(self, state: SpymasterView, *, limit: int = 10) -> list[Clue]:
        """Return up to ``limit`` clues ordered by preference.

        Args:
            state: Full board with hidden colors for the spymaster's team.
            limit: Maximum number of clues to return.

        Returns:
            Clues best-first; empty if no legal clue is available.
        """


@runtime_checkable
class GuessAlgorithm(Protocol):
    """Choose one operative guess or end the guessing phase."""

    def guess_word(self, state: OperativeView) -> GuessAction:
        """Return the next guess or ``GuessAction.end_turn()``.

        Args:
            state: Operative-visible board (no hidden colors on unrevealed cards).

        Returns:
            A word to guess or a pass action.
        """
