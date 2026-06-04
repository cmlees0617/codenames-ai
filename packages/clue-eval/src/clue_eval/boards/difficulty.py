"""Board difficulty scoring from GloVe similarities (per team)."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from clue_eval.boards.types import BoardLayout
from clue_eval.embeddings.store import EmbeddingStore

DEFAULT_BETA = 2.0
_LOG_UNIT = math.log(2.0)  # max of log(1 + c) for c in [0, 1]


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


def _mean_log_nonnegative_similarities(cosines: np.ndarray) -> float | None:
    """Mean ``log(1 + c) / log(2)`` over non-negative cosines; ``None`` if none qualify."""
    valid = cosines[cosines >= 0.0]
    if valid.size == 0:
        return None
    return float(np.mean(np.log1p(valid)) / _LOG_UNIT)


def _mean_log_pairwise_similarity(vectors: np.ndarray) -> float | None:
    count = len(vectors)
    if count < 2:
        return 1.0
    norms = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
    sims = norms @ norms.T
    upper = sims[np.triu_indices(count, k=1)]
    return _mean_log_nonnegative_similarities(upper)


def _mean_log_cross_similarity(left: np.ndarray, right: np.ndarray) -> float | None:
    if len(left) == 0 or len(right) == 0:
        return 0.0
    left_norm = left / np.linalg.norm(left, axis=1, keepdims=True)
    right_norm = right / np.linalg.norm(right, axis=1, keepdims=True)
    cross = left_norm @ right_norm.T
    scored = _mean_log_nonnegative_similarities(cross.ravel())
    return 0.0 if scored is None else scored


def _max_log_assassin_similarity(targets: np.ndarray, assassins: np.ndarray) -> float:
    if len(targets) == 0 or len(assassins) == 0:
        return 0.0
    assassin = assassins[0]
    logged: list[float] = []
    for target in targets:
        cosine = _cosine_similarity(target, assassin)
        if cosine >= 0.0:
            logged.append(float(np.log1p(cosine) / _LOG_UNIT))
    return max(logged) if logged else 0.0


def team_difficulty(
    targets: list[str],
    others: list[str],
    assassins: list[str],
    embeddings: EmbeddingStore,
    *,
    beta: float = DEFAULT_BETA,
) -> float | None:
    """
    Difficulty for one spymaster team in ``[0, 1]`` (higher = harder).

    confusion / (confusion + cohesion)

    Negative cosines are omitted from each aggregate. Returns ``None`` when a team has
    no non-negative target–target pairs (multi-card teams only).

    Similarities use ``log(1 + cos) / log(2)`` on non-negative pairs, which spreads
    scores compared to raw or affine cosine.

    - cohesion: mean log-sim among targets (high → one clue can link them)
    - confusion: mean log-sim(target, other) + beta * max log-sim(target, assassin)
    """
    target_vecs = _vectors(targets, embeddings)
    empty = (0, target_vecs.shape[1])
    other_vecs = _vectors(others, embeddings) if others else np.empty(empty)
    assassin_vecs = _vectors(assassins, embeddings) if assassins else np.empty(empty)

    cohesion = _mean_log_pairwise_similarity(target_vecs)
    if cohesion is None:
        return None
    cross = _mean_log_cross_similarity(target_vecs, other_vecs)
    if cross is None:
        return None
    assassin = _max_log_assassin_similarity(target_vecs, assassin_vecs)

    confusion = cross + beta * assassin
    total = confusion + cohesion
    if total <= 0.0:
        return 0.0
    return float(np.clip(confusion / total, 0.0, 1.0))


def board_difficulty(
    board: BoardLayout,
    embeddings: EmbeddingStore,
    *,
    beta: float = DEFAULT_BETA,
) -> BoardDifficulty | None:
    """
    Compute blue and red spymaster difficulty for ``board``.

    Returns ``None`` if either team lacks any non-negative target–target similarity.
    """
    assassins = board["assassins"]
    blue = team_difficulty(
        board["blues"],
        board["reds"] + board["civilians"] + assassins,
        assassins,
        embeddings,
        beta=beta,
    )
    if blue is None:
        return None
    red = team_difficulty(
        board["reds"],
        board["blues"] + board["civilians"] + assassins,
        assassins,
        embeddings,
        beta=beta,
    )
    if red is None:
        return None
    return BoardDifficulty(blue=blue, red=red)
