"""Batch guess engines for offline operative simulation."""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod

import numpy as np

from clue_eval.embeddings.glove import GloVeEncoder, get_glove_encoder
from clue_eval.embeddings.sentence_transformer import (
    SentenceTransformerEncoder,
    get_sentence_transformer_encoder,
)
from clue_eval.embeddings.store import EmbeddingStore

DEFAULT_SOFTMAX_TEMPERATURE = 0.35
DEFAULT_SOFTMAX_CANDIDATE_MULTIPLIER = 3


def _cosine_scores(clue_vector: np.ndarray, word_vectors: np.ndarray) -> np.ndarray:
    clue_norm = clue_vector / np.linalg.norm(clue_vector)
    word_norms = word_vectors / np.linalg.norm(word_vectors, axis=1, keepdims=True)
    return word_norms @ clue_norm


class OperativeGuessEngine(ABC):
    """Select exactly ``count`` board words for a clue (embedding-space or LLM)."""

    visible_words: list[str]

    def __init__(self) -> None:
        self.visible_words = []

    def update_board_state(self, visible_words: list[str]) -> None:
        self.visible_words = [word.upper() for word in visible_words]

    @abstractmethod
    def guess(self, clue: str, count: int) -> list[str]:
        """Return up to ``count`` guesses, best-first."""


class StaticEmbeddingGuessEngine(OperativeGuessEngine):
    """
    Top-``count`` board words by cosine similarity to the clue in GloVe space.

    Clue phrases are embedded with the full GloVe model; unrevealed board words use
    the packaged Codenames ``words.txt`` vectors.
    """

    def __init__(
        self,
        embeddings: EmbeddingStore,
        *,
        clue_encoder: GloVeEncoder | None = None,
    ) -> None:
        super().__init__()
        self._embeddings = embeddings
        self.clue_encoder = clue_encoder or get_glove_encoder()

    def guess(self, clue: str, count: int) -> list[str]:
        if not self.visible_words or count < 1:
            return []

        count = min(count, len(self.visible_words))
        clue_vector = self.clue_encoder.encode_phrase(clue)
        word_vectors = np.stack(
            [self._embeddings.vector_for(word) for word in self.visible_words],
            axis=0,
        )
        scores = _cosine_scores(clue_vector, word_vectors)
        top_indices = scores.argsort()[-count:][::-1]
        return [self.visible_words[index] for index in top_indices]


class StaticCluegenEmbeddingGuessEngine(OperativeGuessEngine):
    """
    Top-``count`` board words by cosine similarity in cluegen's embedding space.

    Clue and board words both use ``all-MiniLM-L6-v2`` (same as
    :class:`cluegen.clue_engine.ClueEngine`). Sanity-check pairing for
    :class:`cluegen.algorithms.CluegenClueAlgorithm`.
    """

    def __init__(
        self,
        *,
        encoder: SentenceTransformerEncoder | None = None,
    ) -> None:
        super().__init__()
        self.encoder = encoder or get_sentence_transformer_encoder()
        self._word_cache: dict[str, np.ndarray] = {}

    def _word_vector(self, word: str) -> np.ndarray:
        key = word.upper()
        cached = self._word_cache.get(key)
        if cached is not None:
            return cached
        vector = self.encoder.encode_word(key)
        self._word_cache[key] = vector
        return vector

    def guess(self, clue: str, count: int) -> list[str]:
        if not self.visible_words or count < 1:
            return []

        count = min(count, len(self.visible_words))
        clue_vector = self.encoder.encode_phrase(clue)
        word_vectors = np.stack(
            [self._word_vector(word) for word in self.visible_words],
            axis=0,
        )
        scores = _cosine_scores(clue_vector, word_vectors)
        top_indices = scores.argsort()[-count:][::-1]
        return [self.visible_words[index] for index in top_indices]


class SoftmaxEmbeddingGuessEngine(OperativeGuessEngine):
    """
    Sample ``count`` words from a softmax over the top similarity candidates.

    Clue encoding uses the full GloVe model; board words use the packaged store.
    """

    def __init__(
        self,
        embeddings: EmbeddingStore,
        *,
        clue_encoder: GloVeEncoder | None = None,
        temperature: float = DEFAULT_SOFTMAX_TEMPERATURE,
        candidate_multiplier: int = DEFAULT_SOFTMAX_CANDIDATE_MULTIPLIER,
        seed: int | None = None,
    ) -> None:
        super().__init__()
        self._embeddings = embeddings
        self.clue_encoder = clue_encoder or get_glove_encoder()
        self._temperature = temperature
        self._candidate_multiplier = candidate_multiplier
        self._rng = np.random.default_rng(seed)

    def guess(self, clue: str, count: int) -> list[str]:
        if not self.visible_words or count < 1:
            return []

        count = min(count, len(self.visible_words))
        clue_vector = self.clue_encoder.encode_phrase(clue)
        word_vectors = np.stack(
            [self._embeddings.vector_for(word) for word in self.visible_words],
            axis=0,
        )
        scores = _cosine_scores(clue_vector, word_vectors)
        pool_size = min(len(self.visible_words), max(count, count * self._candidate_multiplier))
        top_indices = scores.argsort()[-pool_size:]
        subset_scores = scores[top_indices]
        shifted = subset_scores - float(np.max(subset_scores))
        weights = np.exp(shifted / self._temperature)
        probabilities = weights / float(np.sum(weights))
        chosen = self._rng.choice(top_indices, size=count, replace=False, p=probabilities)
        chosen_sorted = chosen[np.argsort(scores[chosen])[::-1]]
        return [self.visible_words[index] for index in chosen_sorted]


class LlmGuessEngine(OperativeGuessEngine):
    """Local instruct LLM with a strict JSON response schema."""

    def __init__(self, model_name: str = "Qwen/Qwen2.5-0.5B-Instruct") -> None:
        super().__init__()
        from transformers import pipeline

        self._generator = pipeline(
            "text-generation",
            model=model_name,
            device_map="auto",
        )

    def guess(self, clue: str, count: int) -> list[str]:
        if not self.visible_words or count < 1:
            return []

        count = min(count, len(self.visible_words))
        board_list = ", ".join(self.visible_words)
        prompt = (
            "You are playing Codenames as the operative.\n"
            f"Board words (choose ONLY from this list): {board_list}\n"
            f"Clue: {clue.upper()}\n"
            f"Return EXACTLY {count} board words most related to the clue.\n"
            'Respond with ONLY valid JSON matching: {"words": ["WORD1", "WORD2"]}\n'
            f"The words array must have exactly {count} entries, each from the board list, "
            "uppercase, no extra keys or text."
        )
        messages = [{"role": "user", "content": prompt}]
        output = self._generator(
            messages,
            max_new_tokens=64,
            do_sample=False,
            return_full_text=False,
        )
        response_text = str(output[0]["generated_text"]).strip()
        return _parse_llm_words(response_text, self.visible_words, count)


def _parse_llm_words(response_text: str, board_words: list[str], count: int) -> list[str]:
    board_set = set(board_words)
    payload = _extract_json_object(response_text)
    if payload is not None:
        raw_words = payload.get("words", [])
        if isinstance(raw_words, list):
            guesses = [str(word).strip().upper() for word in raw_words if str(word).strip()]
            valid = [word for word in guesses if word in board_set]
            if valid:
                return valid[:count]

    guesses = [word.strip().upper() for word in re.split(r"[,;\n]+", response_text) if word.strip()]
    valid = [word for word in guesses if word in board_set]
    return valid[:count]


def _extract_json_object(text: str) -> dict[str, object] | None:
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        parsed = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None
