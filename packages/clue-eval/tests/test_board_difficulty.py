import numpy as np
import pytest

from clue_eval.boards import BoardFactory
from clue_eval.boards.difficulty import board_difficulty, team_difficulty
from clue_eval.embeddings.store import EmbeddingStore, default_embeddings_path


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
    expected = 1.0 / (0.0 + 2.0 * max_assassin)
    assert team_difficulty(["T1", "T2"], ["O1"], ["AS"], store, beta=2.0) == pytest.approx(
        expected
    )


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
    assert difficulty.blue > 0
    assert difficulty.red > 0


@pytest.mark.skipif(not default_embeddings_path().exists(), reason="embeddings file missing")
def test_generate_uniform_difficulty_boards():
    store = EmbeddingStore.load()
    boards = BoardFactory.generate_uniform_difficulty_boards(5, store, seed=0)
    assert len(boards) == 5
    for index, board in enumerate(boards, start=1):
        assert board["id"] == index
        assert "blue" in board["difficulty"]
        assert "red" in board["difficulty"]

    combined = [(b["difficulty"]["blue"] + b["difficulty"]["red"]) / 2 for b in boards]
    assert combined == sorted(combined)
    assert combined[0] < combined[-1]
