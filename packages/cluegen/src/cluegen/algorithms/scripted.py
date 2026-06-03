"""Fixed clue/guess sequences for tests."""

from __future__ import annotations

from collections import deque

from game_core.types import Clue, GuessAction
from game_core.views import OperativeView, SpymasterView


class ScriptedClueAlgorithm:
    def __init__(self, clues: list[Clue] | None = None) -> None:
        self._clues = deque(clues or [])

    def rank_clues(self, state: SpymasterView, *, limit: int = 10) -> list[Clue]:
        if self._clues:
            clue = self._clues[0]
            return [clue]
        targets = tuple(
            card.word
            for card in state.board
            if not card.revealed and card.color == state.team
        )[:3]
        if not targets:
            return []
        return [Clue(word="TEST", count=len(targets), intended_targets=targets)]


class ScriptedGuessAlgorithm:
    def __init__(self, guesses: list[str | None] | None = None) -> None:
        self._guesses: deque[str | None] = deque(guesses or [])

    def guess_word(self, state: OperativeView) -> GuessAction:
        if not self._guesses:
            unrevealed = [t.word for t in state.board if not t.revealed]
            if unrevealed:
                return GuessAction.guess(unrevealed[0])
            return GuessAction.end_turn()
        next_guess = self._guesses.popleft()
        if next_guess is None:
            return GuessAction.end_turn()
        return GuessAction.guess(next_guess)
