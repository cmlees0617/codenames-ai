import numpy as np
import pytest
from clue_eval.boards.types import BoardLayout
from clue_eval.embeddings.glove import GloVeEncoder
from clue_eval.embeddings.sentence_transformer import SentenceTransformerEncoder
from clue_eval.embeddings.store import EmbeddingStore, default_embeddings_path
from clue_eval.operatives.algorithms import (
    StaticCluegenEmbeddingGuessAlgorithm,
    StaticEmbeddingGuessAlgorithm,
)
from clue_eval.operatives.engines import (
    SoftmaxEmbeddingGuessEngine,
    StaticCluegenEmbeddingGuessEngine,
    StaticEmbeddingGuessEngine,
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


def _test_clue_encoder(store: EmbeddingStore | None = None) -> GloVeEncoder:
    return GloVeEncoder.from_board_store(store or _test_store())


def _fruit_board() -> BoardLayout:
    return {
        "blues": ["APPLE", "PEAR"],
        "reds": ["CAR", "TRAIN"],
        "civilians": ["OCEAN"],
        "assassins": ["TRAIN"],
    }


def test_static_engine_top_k():
    store = _test_store()
    encoder = _test_clue_encoder(store)
    engine = StaticEmbeddingGuessEngine(store, clue_encoder=encoder)
    engine.update_board_state(["APPLE", "PEAR", "CAR"])
    guesses = engine.guess("OCEAN", 2)
    assert guesses == ["APPLE", "PEAR"]


def test_softmax_engine_returns_k_distinct_words():
    store = _test_store()
    encoder = _test_clue_encoder(store)
    engine = SoftmaxEmbeddingGuessEngine(store, clue_encoder=encoder, seed=0)
    engine.update_board_state(["APPLE", "PEAR", "CAR", "TRAIN"])
    guesses = engine.guess("OCEAN", 3)
    assert len(guesses) == 3
    assert len(set(guesses)) == 3


def test_clue_encoder_requires_known_glove_token():
    encoder = _test_clue_encoder()
    vector = encoder.encode_phrase("OCEAN")
    assert vector.shape == (3,)
    assert encoder.can_encode_phrase("OCEAN") is True
    assert encoder.can_encode_phrase("ZZZZUNKNOWN") is False
    with pytest.raises(KeyError):
        encoder.encode_phrase("ZZZZUNKNOWN")


def test_cluegen_embedding_engine_top_k():
    vectors = {
        "APPLE": np.array([1.0, 0.0, 0.0], dtype=np.float32),
        "PEAR": np.array([0.9, 0.1, 0.0], dtype=np.float32),
        "CAR": np.array([0.0, 1.0, 0.0], dtype=np.float32),
        "OCEAN": np.array([0.8, 0.0, 0.2], dtype=np.float32),
    }
    encoder = SentenceTransformerEncoder(
        encode_fn=lambda word: vectors[word.upper()],
    )
    engine = StaticCluegenEmbeddingGuessEngine(encoder=encoder)
    engine.update_board_state(["APPLE", "PEAR", "CAR"])
    assert engine.guess("OCEAN", 2) == ["APPLE", "PEAR"]


def test_create_cluegen_embedding_operative():
    vectors = {
        "APPLE": np.array([1.0, 0.0, 0.0], dtype=np.float32),
        "PEAR": np.array([0.9, 0.1, 0.0], dtype=np.float32),
        "OCEAN": np.array([0.8, 0.0, 0.2], dtype=np.float32),
    }
    encoder = SentenceTransformerEncoder(
        encode_fn=lambda word: vectors[word.upper()],
    )
    algo = create_operative_algorithm("cluegen_embedding", sentence_encoder=encoder)
    assert isinstance(algo, StaticCluegenEmbeddingGuessAlgorithm)


def test_clue_encoder_uses_full_model_not_board_store_only():
    store = _test_store()
    board_encoder = _test_clue_encoder(store)
    assert board_encoder.can_encode_phrase("MARGINS") is False

    full_encoder = GloVeEncoder(
        lookup_fn=lambda word: np.array([1.0, 0.0, 0.0], dtype=np.float32)
        if word.lower() == "margins"
        else None,
    )
    assert full_encoder.can_encode_phrase("MARGINS") is True


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
    algorithm = StaticEmbeddingGuessAlgorithm(store, clue_encoder=_test_clue_encoder(store))
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
        guess_algorithm=StaticEmbeddingGuessAlgorithm(
            _test_store(),
            clue_encoder=_test_clue_encoder(),
        ),
    )
    result = runner.run(scenario)
    assert result["generated_clue"] == "OCEAN"
    assert result["operative"]["team_hit_count"] == 2


def test_create_operative_factory_kinds():
    store = _test_store()
    encoder = _test_clue_encoder(store)
    for kind in ("static_embedding", "softmax_embedding"):
        algo = create_operative_algorithm(kind, embeddings=store, clue_encoder=encoder)
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
    algorithm = StaticEmbeddingGuessAlgorithm(store, clue_encoder=_test_clue_encoder(store))
    result = evaluate_operative_turn(board, "blue", clue, algorithm)
    assert len(result["guesses"]) == 1
