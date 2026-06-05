import random

import numpy as np
from clue_eval.demos.stub_algorithm import StubClueAlgorithm
from clue_eval.embeddings.glove import GloVeEncoder
from clue_eval.embeddings.store import EmbeddingStore
from clue_eval.operatives.algorithms import StaticEmbeddingGuessAlgorithm
from clue_eval.simulation.game import SimulatedGameResult, simulate_game
from clue_eval.simulation.naming import resolve_spymaster_name, sanitize_model_filename
from clue_eval.simulation.results import SimulationBatchResult, results_path_for_model
from clue_eval.simulation.runner import (
    SpymasterSimulationRunner,
    run_spymaster_benchmark_all_operatives,
)
from clue_eval.simulation.state import BoardGameState, spymaster_team_for_board
from game_core.types import Clue
from game_core.views import SpymasterView


def _tiny_board(*, with_difficulty: bool = False):
    board = {
        "id": 99,
        "blues": ["APPLE", "PEAR"],
        "reds": ["CAR"],
        "civilians": ["TABLE"],
        "assassins": ["TRAIN"],
    }
    if with_difficulty:
        board["difficulty"] = {"blue": 0.2, "red": 0.8}
    return board


def _test_clue_encoder(store: EmbeddingStore) -> GloVeEncoder:
    return GloVeEncoder.from_board_store(store)


def _test_store() -> EmbeddingStore:
    return EmbeddingStore(
        words=("APPLE", "PEAR", "CAR", "TABLE", "TRAIN", "LINK"),
        vectors=np.eye(6, dtype=np.float32),
        model="test",
        missing_words=(),
    )


def test_spymaster_team_for_board_picks_larger_side():
    blue_heavy = {"blues": ["A"] * 9, "reds": ["B"] * 8, "civilians": [], "assassins": ["X"]}
    red_heavy = {"blues": ["A"] * 5, "reds": ["B"] * 10, "civilians": [], "assassins": ["X"]}
    assert spymaster_team_for_board(blue_heavy) == "blue"
    assert spymaster_team_for_board(red_heavy) == "red"


def test_simulate_game_uses_red_when_red_has_more_words():
    board = {
        "id": 7,
        "blues": ["ALPHA"],
        "reds": ["BRAVO", "CHARLIE", "DELTA"],
        "civilians": ["ECHO"],
        "assassins": ["FOXTROT"],
    }
    result = simulate_game(
        board,
        StubClueAlgorithm(),
        StaticEmbeddingGuessAlgorithm(
            _test_store(),
            clue_encoder=_test_clue_encoder(_test_store()),
        ),
        rng=random.Random(0),
    )
    assert result.test_team == "red"


def test_simulate_game_records_difficulty():
    board = _tiny_board(with_difficulty=True)
    result = simulate_game(
        board,
        StubClueAlgorithm(),
        StaticEmbeddingGuessAlgorithm(
            _test_store(),
            clue_encoder=_test_clue_encoder(_test_store()),
        ),
        rng=random.Random(0),
    )
    assert result.difficulty_blue == 0.2
    assert result.difficulty_red == 0.8
    assert result.difficulty_mean == 0.5
    assert result.difficulty_test_team == 0.2


def test_simulate_game_win_with_stub():
    board = _tiny_board()
    result = simulate_game(
        board,
        StubClueAlgorithm(),
        StaticEmbeddingGuessAlgorithm(
            _test_store(),
            clue_encoder=_test_clue_encoder(_test_store()),
        ),
        rng=random.Random(0),
    )
    assert result.outcome in {"win", "loss", "abort"}
    assert result.test_team == "blue"


class _IllegalWordClueAlgorithm:
    name = "illegal-word"

    def rank_clues(self, state: SpymasterView, *, limit: int = 10) -> list[Clue]:
        return [Clue(word="APPLE", count=1, intended_targets=())]


class _NoClueAlgorithm:
    name = "no-clue"

    def rank_clues(self, state: SpymasterView, *, limit: int = 10) -> list[Clue]:
        return []


class _UnencodableThenValidClueAlgorithm:
    name = "skip-unencodable"

    def rank_clues(self, state: SpymasterView, *, limit: int = 10) -> list[Clue]:
        targets = tuple(
            card.word
            for card in state.board
            if not card.revealed and card.color == state.team
        )[:2]
        return [
            Clue(word="MARGINS", count=1, intended_targets=targets),
            Clue(word="LINK", count=min(2, len(targets)), intended_targets=targets),
        ]


def test_abort_on_illegal_clue_word():
    board = _tiny_board()
    result = simulate_game(
        board,
        _IllegalWordClueAlgorithm(),
        StaticEmbeddingGuessAlgorithm(
            _test_store(),
            clue_encoder=_test_clue_encoder(_test_store()),
        ),
        rng=random.Random(0),
    )
    assert result.outcome == "abort"
    assert result.abort_reason is not None
    assert result.loss_reason is None


def test_skips_clue_unknown_to_glove_model():
    board = _tiny_board()
    result = simulate_game(
        board,
        _UnencodableThenValidClueAlgorithm(),
        StaticEmbeddingGuessAlgorithm(
            _test_store(),
            clue_encoder=_test_clue_encoder(_test_store()),
        ),
        rng=random.Random(0),
    )
    assert result.outcome != "abort"
    assert result.last_clue == "LINK"


def test_abort_when_spymaster_returns_no_clue():
    board = _tiny_board()
    result = simulate_game(
        board,
        _NoClueAlgorithm(),
        StaticEmbeddingGuessAlgorithm(
            _test_store(),
            clue_encoder=_test_clue_encoder(_test_store()),
        ),
        rng=random.Random(0),
    )
    assert result.outcome == "abort"
    assert "empty" in (result.abort_reason or "").lower()


class _PassEarlyOperative:
    def guess_word(self, state):
        from game_core.types import GuessAction

        return GuessAction.end_turn()


def test_operative_pass_ends_turn_not_abort():
    board = _tiny_board()
    result = simulate_game(
        board,
        StubClueAlgorithm(),
        _PassEarlyOperative(),
        rng=random.Random(0),
    )
    assert result.outcome != "abort"
    assert result.abort_reason is None


class _WrongGuessOperative:
    """First guess hits a civilian; turn should end without abort."""

    def __init__(self) -> None:
        self._calls = 0

    def guess_word(self, state):
        from game_core.types import GuessAction

        self._calls += 1
        return GuessAction.guess("TABLE")


def test_wrong_guess_ends_turn_without_abort():
    operative = _WrongGuessOperative()
    board = _tiny_board()
    result = simulate_game(
        board,
        StubClueAlgorithm(),
        operative,
        rng=random.Random(0),
    )
    assert result.outcome in {"win", "loss"}
    assert operative._calls == 1


def test_opponent_loss_after_one_reveal_on_tiny_board():
    state = BoardGameState.from_layout(_tiny_board())
    assert state.team_words_remaining("red") == 1
    state.reveal_random_opponent_word("blue", random.Random(0))
    assert state.team_words_remaining("red") == 0


def test_resolve_spymaster_name():
    assert resolve_spymaster_name(StubClueAlgorithm()) == "stub-spymaster"
    assert sanitize_model_filename("My Model/v2") == "My_Model_v2"


def test_runner_saves_per_game_records(tmp_path):
    boards = [
        _tiny_board(with_difficulty=True),
        {**_tiny_board(with_difficulty=True), "id": 100, "difficulty": {"blue": 0.9, "red": 0.1}},
    ]
    store = _test_store()
    runner = SpymasterSimulationRunner(
        StubClueAlgorithm(),
        "static_embedding",
        boards=boards,
        guess_algorithm=StaticEmbeddingGuessAlgorithm(
            store,
            clue_encoder=_test_clue_encoder(store),
        ),
        show_progress=False,
    )
    path = runner.run_and_save(tmp_path / "stub-spymaster_static_embedding.json")
    payload = path.read_text(encoding="utf-8")
    assert "stub-spymaster" in payload
    assert '"board_count": 2' in payload
    assert "difficulty_mean" in payload
    assert '"games"' in payload


def test_benchmark_all_operatives_writes_three_files(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "clue_eval.simulation.results.default_results_dir",
        lambda: tmp_path,
    )

    def _fake_create(_kind, **_kwargs):
        store = _test_store()
        return StaticEmbeddingGuessAlgorithm(
            store,
            clue_encoder=_test_clue_encoder(store),
        )

    monkeypatch.setattr(
        "clue_eval.simulation.runner.create_operative_algorithm",
        _fake_create,
    )
    boards = [_tiny_board(with_difficulty=True)]
    paths = run_spymaster_benchmark_all_operatives(
        StubClueAlgorithm(),
        boards=boards,
        show_progress=False,
    )
    assert len(paths) == 3
    for kind in ("static_embedding", "softmax_embedding", "llm"):
        path = tmp_path / f"stub-spymaster_{kind}.json"
        assert path in paths
        text = path.read_text(encoding="utf-8")
        assert f'"{kind}"' in text


def test_results_path_includes_spymaster_and_operative():
    path = results_path_for_model("my-model", "llm")
    assert path.name == "my-model_llm.json"


def test_results_path_sample_suffix():
    path = results_path_for_model("cluegen", "static_embedding", sample_size=25)
    assert path.name == "cluegen_static_embedding_sample25.json"


def test_batch_summary():
    batch = SimulationBatchResult(
        spymaster_name="test",
        operative_kind="static_embedding",
        games=(
            SimulatedGameResult(
                1,
                "win",
                "blue",
                3,
                2,
                difficulty_mean=0.5,
            ),
            SimulatedGameResult(
                2,
                "loss",
                "blue",
                4,
                8,
                loss_reason="opponent",
                difficulty_mean=0.7,
            ),
            SimulatedGameResult(
                3,
                "abort",
                "blue",
                1,
                0,
                abort_reason="bad",
                difficulty_mean=0.3,
            ),
        ),
    )
    assert batch.summary() == {"win": 1, "loss": 1, "abort": 1}
