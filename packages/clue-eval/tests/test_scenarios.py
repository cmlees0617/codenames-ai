from game_core.types import Clue

from clue_eval.demos.stub_algorithm import StubClueAlgorithm
from clue_eval.scenarios.runner import ScenarioRunner
from clue_eval.scenarios.types import Scenario


def _minimal_board() -> dict:
    return {
        "blues": ["ALPHA", "BRAVO"],
        "reds": ["CHARLIE", "DELTA"],
        "civilians": ["ECHO"],
        "assassins": ["FOXTROT"],
    }


def test_scenario_runner_returns_clue():
    scenario = Scenario(name="smoke", board=_minimal_board())
    result = ScenarioRunner(StubClueAlgorithm()).run(scenario)

    assert result["name"] == "smoke"
    assert result["generated_clue"] == "TEST"
    assert result["targets_covered"] == ["ALPHA", "BRAVO"]
    assert result["pass"] is None


def test_scenario_runner_grading():
    scenario = Scenario(
        name="graded",
        board=_minimal_board(),
        expected_targets=frozenset({"ALPHA"}),
    )
    result = ScenarioRunner(StubClueAlgorithm()).run(scenario)
    assert result["pass"] is True


def test_scenario_runner_custom_clue_list():
    class FixedClueAlgorithm:
        def rank_clues(self, state, *, limit: int = 10) -> list[Clue]:
            return [Clue(word="CUSTOM", count=1, intended_targets=("ALPHA",))]

    result = ScenarioRunner(FixedClueAlgorithm()).run(
        Scenario(name="fixed", board=_minimal_board()),
    )
    assert result["generated_clue"] == "CUSTOM"
    assert result["targets_covered"] == ["ALPHA"]
