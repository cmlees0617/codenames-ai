"""Factory for the three packaged operative test conditions."""

from __future__ import annotations

from typing import Literal

from game_core.algorithms import GuessAlgorithm

from clue_eval.embeddings.store import EmbeddingStore
from clue_eval.operatives.algorithms import (
    LlmGuessAlgorithm,
    SoftmaxEmbeddingGuessAlgorithm,
    StaticEmbeddingGuessAlgorithm,
)

OperativeKind = Literal["static_embedding", "softmax_embedding", "llm"]

OPERATIVE_KINDS: tuple[OperativeKind, ...] = (
    "static_embedding",
    "softmax_embedding",
    "llm",
)


def create_operative_algorithm(
    kind: OperativeKind,
    *,
    embeddings: EmbeddingStore | None = None,
    softmax_temperature: float = 0.35,
    softmax_seed: int | None = None,
    llm_model_name: str = "Qwen/Qwen2.5-0.5B-Instruct",
) -> GuessAlgorithm:
    """
    Build one of the standard clue-eval operative agents.

    Used as a fixed test condition when evaluating candidate spymaster models.
    """
    if kind == "static_embedding":
        return StaticEmbeddingGuessAlgorithm(embeddings)
    if kind == "softmax_embedding":
        return SoftmaxEmbeddingGuessAlgorithm(
            embeddings,
            temperature=softmax_temperature,
            seed=softmax_seed,
        )
    if kind == "llm":
        return LlmGuessAlgorithm(model_name=llm_model_name)
    raise ValueError(f"Unknown operative kind: {kind!r}")
