"""Operative :class:`~game_core.algorithms.GuessAlgorithm` adapters for clue-eval."""

from __future__ import annotations

from game_core.types import GuessAction
from game_core.views import OperativeView

from clue_eval.embeddings.glove import GloVeEncoder, get_glove_encoder
from clue_eval.embeddings.sentence_transformer import (
    SentenceTransformerEncoder,
    get_sentence_transformer_encoder,
)
from clue_eval.embeddings.store import EmbeddingStore
from clue_eval.operatives.engines import (
    LlmGuessEngine,
    OperativeGuessEngine,
    SoftmaxEmbeddingGuessEngine,
    StaticCluegenEmbeddingGuessEngine,
    StaticEmbeddingGuessEngine,
)


class _QueuedGuessAlgorithm:
    """Pop one guess at a time from a batch engine queue (per clue)."""

    def __init__(self, engine: OperativeGuessEngine) -> None:
        self._engine = engine
        self._pending: list[str] = []
        self._clue_key: tuple[str, int] | None = None

    def supports_clue_word(self, clue_word: str) -> bool:
        """Whether this operative can guess from ``clue_word`` (always true by default)."""
        return True

    def _visible_words(self, state: OperativeView) -> list[str]:
        return [tile.word for tile in state.board if not tile.revealed]

    def _refresh_queue(self, state: OperativeView) -> None:
        clue = state.current_clue
        if clue is None or clue.count < 1:
            self._pending = []
            self._clue_key = None
            return

        key = (clue.word.upper(), clue.count)
        if key == self._clue_key and self._pending:
            return

        visible = self._visible_words(state)
        self._engine.update_board_state(visible)
        try:
            self._pending = list(self._engine.guess(clue.word, clue.count))
        except KeyError:
            self._pending = []
        self._clue_key = key

    def guess_word(self, state: OperativeView) -> GuessAction:
        if state.guesses_remaining <= 0:
            return GuessAction.end_turn()

        self._refresh_queue(state)
        if not self._pending:
            return GuessAction.end_turn()

        return GuessAction.guess(self._pending.pop(0))


class _EmbeddingGuessAlgorithm(_QueuedGuessAlgorithm):
    """Shared full-GloVe clue encoding check for static and softmax operatives."""

    _clue_encoder: GloVeEncoder

    def supports_clue_word(self, clue_word: str) -> bool:
        return self._clue_encoder.can_encode_phrase(clue_word)


class StaticEmbeddingGuessAlgorithm(_EmbeddingGuessAlgorithm):
    """Top-K GloVe cosine guesses (fixed embedding space)."""

    def __init__(
        self,
        embeddings: EmbeddingStore | None = None,
        *,
        clue_encoder: GloVeEncoder | None = None,
    ) -> None:
        store = embeddings if embeddings is not None else EmbeddingStore.load()
        encoder = clue_encoder or get_glove_encoder()
        self._embeddings = store
        self._clue_encoder = encoder
        super().__init__(StaticEmbeddingGuessEngine(store, clue_encoder=encoder))


class SoftmaxEmbeddingGuessAlgorithm(_EmbeddingGuessAlgorithm):
    """Stochastic GloVe guesses sampled from a softmax over top candidates."""

    def __init__(
        self,
        embeddings: EmbeddingStore | None = None,
        *,
        clue_encoder: GloVeEncoder | None = None,
        temperature: float = 0.35,
        candidate_multiplier: int = 3,
        seed: int | None = None,
    ) -> None:
        store = embeddings if embeddings is not None else EmbeddingStore.load()
        encoder = clue_encoder or get_glove_encoder()
        self._embeddings = store
        self._clue_encoder = encoder
        super().__init__(
            SoftmaxEmbeddingGuessEngine(
                store,
                clue_encoder=encoder,
                temperature=temperature,
                candidate_multiplier=candidate_multiplier,
                seed=seed,
            )
        )


class StaticCluegenEmbeddingGuessAlgorithm(_QueuedGuessAlgorithm):
    """
    Top-K guesses in cluegen's sentence-transformer space (sanity-check operative).

    Pair with :class:`cluegen.algorithms.CluegenClueAlgorithm` to verify the
    benchmark pipeline in a shared embedding space.
    """

    def __init__(
        self,
        *,
        encoder: SentenceTransformerEncoder | None = None,
    ) -> None:
        encoder = encoder or get_sentence_transformer_encoder()
        self._encoder = encoder
        super().__init__(StaticCluegenEmbeddingGuessEngine(encoder=encoder))

    def supports_clue_word(self, clue_word: str) -> bool:
        return self._encoder.can_encode_phrase(clue_word)


class LlmGuessAlgorithm(_QueuedGuessAlgorithm):
    """Local LLM operative with enforced JSON word list output."""

    def __init__(self, model_name: str = "Qwen/Qwen2.5-0.5B-Instruct") -> None:
        super().__init__(LlmGuessEngine(model_name=model_name))
