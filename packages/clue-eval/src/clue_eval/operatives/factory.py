"""Factory for the packaged operative test conditions."""

from __future__ import annotations

from typing import Literal

from game_core.algorithms import GuessAlgorithm

from clue_eval.embeddings.glove import GloVeEncoder, get_glove_encoder
from clue_eval.embeddings.sentence_transformer import (
    SentenceTransformerEncoder,
    get_sentence_transformer_encoder,
)
from clue_eval.embeddings.store import EmbeddingStore
from clue_eval.operatives.algorithms import (
    LlmGuessAlgorithm,
    SoftmaxEmbeddingGuessAlgorithm,
    StaticCluegenEmbeddingGuessAlgorithm,
    StaticEmbeddingGuessAlgorithm,
)

OperativeKind = Literal[
    "static_embedding",
    "softmax_embedding",
    "llm",
    "cluegen_embedding",
]

# Default full benchmark (3 × 5000 games).
OPERATIVE_KINDS: tuple[OperativeKind, ...] = (
    "static_embedding",
    "softmax_embedding",
    "llm",
)

# All selectable operatives (includes cluegen-aligned sanity check).
SELECTABLE_OPERATIVE_KINDS: tuple[OperativeKind, ...] = OPERATIVE_KINDS + (
    "cluegen_embedding",
)


def create_operative_algorithm(
    kind: OperativeKind,
    *,
    embeddings: EmbeddingStore | None = None,
    clue_encoder: GloVeEncoder | None = None,
    sentence_encoder: SentenceTransformerEncoder | None = None,
    softmax_temperature: float = 0.35,
    softmax_seed: int | None = None,
    llm_model_name: str = "Qwen/Qwen2.5-0.5B-Instruct",
) -> GuessAlgorithm:
    """
    Build one of the standard clue-eval operative agents.

    Used as a fixed test condition when evaluating candidate spymaster models.
    """
    if kind == "cluegen_embedding":
        encoder = sentence_encoder or get_sentence_transformer_encoder()
        return StaticCluegenEmbeddingGuessAlgorithm(encoder=encoder)

    glove = clue_encoder or get_glove_encoder()
    if kind == "static_embedding":
        return StaticEmbeddingGuessAlgorithm(embeddings, clue_encoder=glove)
    if kind == "softmax_embedding":
        return SoftmaxEmbeddingGuessAlgorithm(
            embeddings,
            clue_encoder=glove,
            temperature=softmax_temperature,
            seed=softmax_seed,
        )
    if kind == "llm":
        return LlmGuessAlgorithm(model_name=llm_model_name)
    raise ValueError(f"Unknown operative kind: {kind!r}")
