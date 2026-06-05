"""Full GloVe lookups for clue encoding (board words use packaged :class:`EmbeddingStore`)."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

import numpy as np

from clue_eval.embeddings.store import MODEL_NAME, VECTOR_SIZE, EmbeddingStore

LookupFn = Callable[[str], np.ndarray | None]

_shared_encoder = None


def _clue_tokens(text: str) -> list[str]:
    return [token for token in re.split(r"[\s\-]+", text.strip().upper()) if token]


def lookup_vector(model: Any, word: str) -> np.ndarray | None:
    """Resolve a GloVe vector; multi-word phrases use the mean of known tokens."""
    key = word.lower()
    if key in model:
        return np.asarray(model[key], dtype=np.float32)

    tokens = key.split()
    if len(tokens) < 2:
        return None

    token_vectors = [
        np.asarray(model[token], dtype=np.float32) for token in tokens if token in model
    ]
    if not token_vectors:
        return None
    return np.mean(token_vectors, axis=0).astype(np.float32)


class GloVeEncoder:
    """
    Encode arbitrary clue phrases in the full ``glove-wiki-gigaword-300`` model.

    Board-word similarity still uses the packaged :class:`~clue_eval.embeddings.store.EmbeddingStore`
    (Codenames ``words.txt`` only).
    """

    def __init__(
        self,
        *,
        model: Any | None = None,
        lookup_fn: LookupFn | None = None,
    ) -> None:
        self._model = model
        self._lookup_fn = lookup_fn

    @classmethod
    def from_board_store(cls, store: EmbeddingStore) -> GloVeEncoder:
        """Test helper: encode clues using only vectors from a packaged board store."""

        def lookup(word: str) -> np.ndarray | None:
            try:
                return store.vector_for(word)
            except KeyError:
                return None

        return cls(lookup_fn=lookup)

    def _resolve_token(self, token: str) -> np.ndarray | None:
        if self._lookup_fn is not None:
            return self._lookup_fn(token)

        model = self._ensure_model()
        return lookup_vector(model, token)

    def _ensure_model(self) -> Any:
        if self._model is not None:
            return self._model
        import gensim.downloader as api

        self._model = api.load(MODEL_NAME)
        if getattr(self._model, "vector_size", None) not in (None, VECTOR_SIZE):
            raise ValueError(
                f"Expected {VECTOR_SIZE}-dimensional vectors, got {self._model.vector_size}"
            )
        return self._model

    def can_encode_phrase(self, text: str) -> bool:
        """True when at least one clue token has a vector in the full GloVe model."""
        return any(self._resolve_token(token) is not None for token in _clue_tokens(text))

    def encode_phrase(self, text: str) -> np.ndarray:
        """Mean GloVe vector for clue tokens known to the full model."""
        vectors = [
            vector
            for token in _clue_tokens(text)
            if (vector := self._resolve_token(token)) is not None
        ]
        if not vectors:
            raise KeyError(f"No GloVe embedding for clue phrase {text!r}")
        return np.mean(vectors, axis=0).astype(np.float32)


def load_gensim_model() -> Any:
    """Load ``glove-wiki-gigaword-300`` via gensim (used when building board store)."""
    return GloVeEncoder()._ensure_model()


def get_glove_encoder() -> GloVeEncoder:
    """Return the process-wide lazy-loaded GloVe encoder for clue phrases."""
    global _shared_encoder
    if _shared_encoder is None:
        _shared_encoder = GloVeEncoder()
    return _shared_encoder
