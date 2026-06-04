import math

import numpy as np
import pytest
from clue_eval.boards import BoardFactory
from clue_eval.boards.difficulty import (
    _LOG_UNIT,
    board_difficulty,
    team_difficulty,
)
from clue_eval.embeddings.store import (
    EmbeddingStore,
    default_embeddings_path,
)


def _log_unit(cosine: float) -> float:
    return math.log1p(cosine) / _LOG_UNIT


def test_team_difficulty_formula():
    store = EmbeddingStore(
        words=("T1", "T2", "O1", "AS"),
        vectors=np.array(
            [[1.0, 0.0], [1.0, 0.0], [0.0, 1.0], [0.9, 0.1]],
            dtype=np.float32,
        ),
        model="test",
        missing_words=(),
    )
    assassin_vec = store.vector_for("AS")
    max_assassin = float(
        np.dot([1.0, 0.0], assassin_vec) / (1.0 * np.linalg.norm(assassin_vec))
    )
    cohesion = _log_unit(1.0)
    confusion = _log_unit(0.0) + 2.0 * _log_unit(max_assassin)
    expected_easy = confusion / (confusion + cohesion)
    assert team_difficulty(["T1", "T2"], ["O1"], ["AS"], store, beta=2.0) == pytest.approx(
        expected_easy
    )
    assert 0.0 <= expected_easy <= 1.0

    hard_store = EmbeddingStore(
        words=("A", "B", "C"),
        vectors=np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 0.0]], dtype=np.float32),
        model="test",
        missing_words=(),
    )
    easy_score = team_difficulty(["T1", "T2"], ["O1"], ["AS"], store, beta=2.0)
    hard_score = team_difficulty(["A", "B"], ["C"], [], hard_store, beta=2.0)
    assert hard_score is not None and easy_score is not None
    assert hard_score > easy_score


def test_all_negative_target_pairs_returns_none():
    store = EmbeddingStore(
        words=("T1", "T2"),
        vectors=np.array([[1.0, 0.0], [-1.0, 0.0]], dtype=np.float32),
        model="test",
        missing_words=(),
    )
    assert team_difficulty(["T1", "T2"], [], [], store, beta=2.0) is None


def test_negative_cross_omitted_not_rejected():
    store = EmbeddingStore(
        words=("T", "O", "A"),
        vectors=np.array(
            [[1.0, 0.0], [-1.0, 0.0], [0.0, 1.0]],
            dtype=np.float32,
        ),
        model="test",
        missing_words=(),
    )
    score = team_difficulty(["T"], ["O"], ["A"], store, beta=2.0)
    assert score is not None
    assert 0.0 <= score <= 1.0


@pytest.mark.skipif(not default_embeddings_path().exists(), reason="embeddings file missing")
def test_board_difficulty_both_teams():
    store = EmbeddingStore.load()
    board = {
        "blues": list(store.words[:9]),
        "reds": list(store.words[9:17]),
        "civilians": list(store.words[17:24]),
        "assassins": [store.words[24]],
    }
    difficulty = board_difficulty(board, store)
    assert difficulty is not None
    assert 0.0 <= difficulty.blue <= 1.0
    assert 0.0 <= difficulty.red <= 1.0


@pytest.mark.skipif(not default_embeddings_path().exists(), reason="embeddings file missing")
def test_log_difficulty_wider_spread_than_affine_on_random_boards():
    """Log scoring should use more of [0, 1] than (cos+1)/2 on typical random layouts."""
    store = EmbeddingStore.load()
    rng = np.random.default_rng(0)
    words = list(store.words)
    log_scores: list[float] = []
    affine_scores: list[float] = []

    for _ in range(200):
        sample = rng.choice(len(words), size=25, replace=False)
        board = {
            "blues": [words[i] for i in sample[:9]],
            "reds": [words[i] for i in sample[9:17]],
            "civilians": [words[i] for i in sample[17:24]],
            "assassins": [words[sample[24]]],
        }
        scored = board_difficulty(board, store)
        if scored is None:
            continue
        log_scores.append((scored.blue + scored.red) / 2.0)
        affine_scores.append(_affine_mean_difficulty(board, store))

    assert len(log_scores) >= 50
    log_span = max(log_scores) - min(log_scores)
    affine_span = max(affine_scores) - min(affine_scores)
    assert log_span > affine_span


def _affine_mean_difficulty(board, store: EmbeddingStore) -> float:
    from clue_eval.boards.types import BoardLayout

    layout: BoardLayout = board
    assassins = layout["assassins"]
    blue_others = layout["reds"] + layout["civilians"] + assassins
    red_others = layout["blues"] + layout["civilians"] + assassins
    blue = _affine_team(layout["blues"], blue_others, assassins, store)
    red = _affine_team(layout["reds"], red_others, assassins, store)
    return (blue + red) / 2.0


def _affine_team(targets, others, assassins, store, *, beta: float = 2.0) -> float:
    def unit(c: float) -> float:
        return (c + 1.0) / 2.0

    def vecs(words):
        return np.stack([store.vector_for(w) for w in words], axis=0)

    t = vecs(targets)
    o = vecs(others) if others else np.empty((0, t.shape[1]))
    a = vecs(assassins) if assassins else np.empty((0, t.shape[1]))

    if len(t) < 2:
        cohesion = 1.0
    else:
        tn = t / np.linalg.norm(t, axis=1, keepdims=True)
        sims = tn @ tn.T
        cohesion = unit(float(np.mean(sims[np.triu_indices(len(t), k=1)])))

    if len(o) == 0:
        cross = 0.0
    else:
        tn = t / np.linalg.norm(t, axis=1, keepdims=True)
        on = o / np.linalg.norm(o, axis=1, keepdims=True)
        cross = unit(float(np.mean(tn @ on.T)))

    if len(a) == 0:
        assassin = 0.0
    else:
        assassin = unit(
            max(
                float(np.dot(tv, a[0]) / (np.linalg.norm(tv) * np.linalg.norm(a[0])))
                for tv in t
            )
        )

    confusion = cross + beta * assassin
    return confusion / (confusion + cohesion)


@pytest.mark.skipif(not default_embeddings_path().exists(), reason="embeddings file missing")
def test_generate_uniform_difficulty_boards():
    store = EmbeddingStore.load()
    boards = BoardFactory.generate_uniform_difficulty_boards(5, store, seed=0)
    assert len(boards) == 5
    for index, board in enumerate(boards, start=1):
        assert board["id"] == index
        assert "blue" in board["difficulty"]
        assert "red" in board["difficulty"]
        assert 0.0 <= board["difficulty"]["blue"] <= 1.0
        assert 0.0 <= board["difficulty"]["red"] <= 1.0

    combined = [(b["difficulty"]["blue"] + b["difficulty"]["red"]) / 2 for b in boards]
    assert combined == sorted(combined)
    assert combined[0] < combined[-1]
