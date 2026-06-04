"""Operative guess algorithms."""

from __future__ import annotations

import random

from game_core.types import GuessAction
from game_core.views import OperativeView

from cluegen.operative import EmbeddingOperative


class EmbeddingGuessAlgorithm:
    """Guess one word at a time using embedding similarity to the current clue."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self._operative = EmbeddingOperative(model_name=model_name)
        self._pending: list[str] = []
        self._clue_key: tuple[str, int] | None = None

    def _visible_words(self, state: OperativeView) -> list[str]:
        return [tile.word for tile in state.board if not tile.revealed]

    def _refresh_queue(self, state: OperativeView) -> None:
        clue = state.current_clue
        if clue is None or clue.count < 1:
            self._pending = []
            self._clue_key = None
            return

        key = (clue.word, clue.count)
        if key == self._clue_key and self._pending:
            return

        visible = self._visible_words(state)
        self._operative.update_board_state(visible)  # type: ignore[no-untyped-call]
        self._pending = list(self._operative.guess(clue.word, clue.count))
        self._clue_key = key

    def guess_word(self, state: OperativeView) -> GuessAction:
        if state.guesses_remaining <= 0:
            return GuessAction.end_turn()

        self._refresh_queue(state)
        if not self._pending:
            return GuessAction.end_turn()

        return GuessAction.guess(self._pending.pop(0))


class RandomGuessAlgorithm:
    """Pick a random unrevealed tile (useful for tests and simple bots)."""

    def guess_word(self, state: OperativeView) -> GuessAction:
        if state.guesses_remaining <= 0:
            return GuessAction.end_turn()
        unrevealed = [tile.word for tile in state.board if not tile.revealed]
        if not unrevealed:
            return GuessAction.end_turn()
        return GuessAction.guess(random.choice(unrevealed))
