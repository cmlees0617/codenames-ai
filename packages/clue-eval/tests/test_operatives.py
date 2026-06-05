import numpy as np
import pytest
from clue_eval.boards.types import BoardLayout
from clue_eval.embeddings.store import EmbeddingStore, default_embeddings_path
from clue_eval.operatives.algorithms import (
    StaticEmbeddingGuessAlgorithm,
)
from clue_eval.operatives.engines import (
    SoftmaxEmbeddingGuessEngine,
    StaticEmbeddingGuessEngine,
    encode_phrase,
)
from clue_eval.operatives.factory import create_operative_algorithm
from clue_eval.operatives.scoring import score_operative_guesses
from clue_eval.operatives.simulation import collect_operative_guesses, evaluate_operative_turn
from clue_eval.scenarios.runner import ScenarioRunner
from clue_eval.scenarios.types import Scenario
from game_core.types import Clue


def _test_store() -> EmbeddingStore:
    return EmbeddingStore(
        words=("APPLE", "PEAR", "CAR", "TRAIN", "OCEAN"),
        vectors=np.array(
            [
                [1.0, 0.0, 0.0],
                [0.9, 0.1, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.9, 0.1],
                [0.8, 0.0, 0.2],
            ],
            dtype=np.float32,
        ),
        model="test",
        missing_words=(),
    )


def _fruit_board() -> BoardLayout:
    return {
        "blues": ["APPLE", "PEAR"],
        "reds": ["CAR", "TRAIN"],
        "civilians": ["OCEAN"],
        "assassins": ["TRAIN"],
    }


def test_static_engine_top_k():
    store = _test_store()
    engine = StaticEmbeddingGuessEngine(store)
    engine.update_board_state(["APPLE", "PEAR", "CAR"])
    guesses = engine.guess("OCEAN", 2)
    assert guesses == ["APPLE", "PEAR"]


def test_softmax_engine_returns_k_distinct_words():
    store = _test_store()
    engine = SoftmaxEmbeddingGuessEngine(store, seed=0)
    engine.update_board_state(["APPLE", "PEAR", "CAR", "TRAIN"])
    guesses = engine.guess("OCEAN", 3)
    assert len(guesses) == 3
    assert len(set(guesses)) == 3


def test_encode_phrase_requires_known_token():
    store = _test_store()
    vector = encode_phrase(store, "OCEAN")
    assert vector.shape == (3,)
    with pytest.raises(KeyError):
        encode_phrase(store, "ZZZZUNKNOWN")


def test_score_operative_guesses():
    board = _fruit_board()
    scoring = score_operative_guesses(board, "blue", ["APPLE", "CAR"])
    assert scoring["team_hit_count"] == 1
    assert scoring["team_hits"] == ["APPLE"]
    assert "CAR" in scoring["opponent_hits"]


def test_collect_operative_guesses_via_algorithm():
    store = _test_store()
    board: BoardLayout = {
        "blues": ["APPLE", "PEAR"],
        "reds": ["CAR"],
        "civilians": [],
        "assassins": [],
    }
    clue = Clue(word="OCEAN", count=2, intended_targets=("APPLE", "PEAR"))
    algorithm = StaticEmbeddingGuessAlgorithm(store)
    guesses = collect_operative_guesses(board, "blue", clue, algorithm)
    assert guesses == ["APPLE", "PEAR"]


class _FixedClueAlgorithm:
    def __init__(self, clues: list[Clue]) -> None:
        self._clues = clues

    def rank_clues(self, state, *, limit: int = 10) -> list[Clue]:
        return self._clues[:limit]


def test_scenario_runner_with_static_operative():
    board: BoardLayout = {
        "blues": ["APPLE", "PEAR"],
        "reds": ["CAR"],
        "civilians": [],
        "assassins": [],
    }
    scenario = Scenario(name="operative-smoke", board=board, team="blue", clue_limit=1)
    clue = Clue(word="OCEAN", count=2, intended_targets=("APPLE", "PEAR"))
    spymaster = _FixedClueAlgorithm([clue])
    runner = ScenarioRunner(
        spymaster,
        guess_algorithm=StaticEmbeddingGuessAlgorithm(_test_store()),
    )
    result = runner.run(scenario)
    assert result["generated_clue"] == "OCEAN"
    assert result["operative"]["team_hit_count"] == 2


def test_create_operative_factory_kinds():
    store = _test_store()
    for kind in ("static_embedding", "softmax_embedding"):
        algo = create_operative_algorithm(kind, embeddings=store)
        assert hasattr(algo, "guess_word")


@pytest.mark.skipif(not default_embeddings_path().exists(), reason="embeddings file missing")
def test_evaluate_operative_with_packaged_glove():
    store = EmbeddingStore.load()
    board = {
        "blues": list(store.words[:2]),
        "reds": list(store.words[2:4]),
        "civilians": [store.words[4]],
        "assassins": [store.words[5]],
    }
    clue = Clue(word=store.words[0], count=1, intended_targets=(store.words[0],))
    algorithm = StaticEmbeddingGuessAlgorithm(store)
    result = evaluate_operative_turn(board, "blue", clue, algorithm)
    assert len(result["guesses"]) == 1
