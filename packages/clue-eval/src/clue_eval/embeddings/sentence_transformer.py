"""Sentence-transformer encoding for cluegen-aligned operative sanity checks."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

import numpy as np

# Default for :class:`cluegen.clue_engine.ClueEngine`.
DEFAULT_CLUEGEN_MODEL = "all-MiniLM-L6-v2"

_shared_encoder = None


def _clue_tokens(text: str) -> list[str]:
    return [token for token in re.split(r"[\s\-]+", text.strip().upper()) if token]


class SentenceTransformerEncoder:
    """
    Encode clue and board words with the same model cluegen uses.

    Uses ``all-MiniLM-L6-v2`` by default (see :class:`cluegen.clue_engine.ClueEngine`).
    """

    def __init__(
        self,
        *,
        model_name: str = DEFAULT_CLUEGEN_MODEL,
        model: Any | None = None,
        encode_fn: Callable[[str], np.ndarray] | None = None,
    ) -> None:
        self._model_name = model_name
        self._model = model
        self._encode_fn = encode_fn

    def encode_word(self, word: str) -> np.ndarray:
        """Encode one board or clue token (uppercase, matching cluegen)."""
        if self._encode_fn is not None:
            return self._encode_fn(word.upper())
        model = self._ensure_model()
        return np.asarray(model.encode(word.upper()), dtype=np.float32)

    def encode_phrase(self, text: str) -> np.ndarray:
        """Mean sentence-transformer vector for clue tokens."""
        tokens = _clue_tokens(text)
        if not tokens:
            raise KeyError(f"No tokens in clue phrase {text!r}")
        vectors = [self.encode_word(token) for token in tokens]
        return np.mean(vectors, axis=0).astype(np.float32)

    def can_encode_phrase(self, text: str) -> bool:
        """Sentence-transformers can embed arbitrary clue text."""
        return bool(_clue_tokens(text))

    def _ensure_model(self) -> Any:
        if self._model is not None:
            return self._model
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(self._model_name)
        return self._model


def get_sentence_transformer_encoder(
    *,
    model_name: str = DEFAULT_CLUEGEN_MODEL,
) -> SentenceTransformerEncoder:
    """Return the process-wide lazy-loaded cluegen-aligned encoder."""
    global _shared_encoder
    if _shared_encoder is None or _shared_encoder._model_name != model_name:
        _shared_encoder = SentenceTransformerEncoder(model_name=model_name)
    return _shared_encoder
