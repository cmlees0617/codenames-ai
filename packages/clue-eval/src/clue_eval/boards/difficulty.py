"""Board difficulty scoring from GloVe similarities (per team)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from clue_eval.boards.types import BoardLayout
from clue_eval.embeddings.store import EmbeddingStore

DEFAULT_BETA = 2.0


@dataclass(frozen=True, slots=True)
class BoardDifficulty:
    """Semantic difficulty for each spymaster side on a 25-card board."""

    blue: float
    red: float

    def as_dict(self) -> dict[str, float]:
        return {"blue": self.blue, "red": self.red}


def _vectors(words: list[str], embeddings: EmbeddingStore) -> np.ndarray:
    return np.stack([embeddings.vector_for(word) for word in words], axis=0)


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def _mean_pairwise_similarity(vectors: np.ndarray) -> float:
    count = len(vectors)
    if count < 2:
        return 1.0
    norms = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
    sims = norms @ norms.T
    upper = sims[np.triu_indices(count, k=1)]
    return float(np.mean(upper))


def _mean_cross_similarity(left: np.ndarray, right: np.ndarray) -> float:
    if len(left) == 0 or len(right) == 0:
        return 0.0
    left_norm = left / np.linalg.norm(left, axis=1, keepdims=True)
    right_norm = right / np.linalg.norm(right, axis=1, keepdims=True)
    return float(np.mean(left_norm @ right_norm.T))


def _max_similarity_to_assassin(targets: np.ndarray, assassins: np.ndarray) -> float:
    if len(targets) == 0 or len(assassins) == 0:
        return 0.0
    return max(_cosine_similarity(target, assassins[0]) for target in targets)


def team_difficulty(
    targets: list[str],
    others: list[str],
    assassins: list[str],
    embeddings: EmbeddingStore,
    *,
    beta: float = DEFAULT_BETA,
) -> float:
    """
    Difficulty for one spymaster team.

    avg_sim(target, target) / (avg_sim(target, other) + beta * max_sim(target, assassin))
    """
    target_vecs = _vectors(targets, embeddings)
    empty = (0, target_vecs.shape[1])
    other_vecs = _vectors(others, embeddings) if others else np.empty(empty)
    assassin_vecs = _vectors(assassins, embeddings) if assassins else np.empty(empty)

    numerator = _mean_pairwise_similarity(target_vecs)
    target_other = _mean_cross_similarity(target_vecs, other_vecs)
    assassin_penalty = beta * _max_similarity_to_assassin(target_vecs, assassin_vecs)
    denominator = target_other + assassin_penalty
    if denominator <= 0.0:
        return float("inf")
    return numerator / denominator


def board_difficulty(
    board: BoardLayout,
    embeddings: EmbeddingStore,
    *,
    beta: float = DEFAULT_BETA,
) -> BoardDifficulty:
    """Compute blue and red spymaster difficulty for ``board``."""
    assassins = board["assassins"]
    return BoardDifficulty(
        blue=team_difficulty(
            board["blues"],
            board["reds"] + board["civilians"] + assassins,
            assassins,
            embeddings,
            beta=beta,
        ),
        red=team_difficulty(
            board["reds"],
            board["blues"] + board["civilians"] + assassins,
            assassins,
            embeddings,
            beta=beta,
        ),
    )
