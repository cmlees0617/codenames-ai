"""Run predefined test suites against any :class:`~game_core.algorithms.ClueAlgorithm`."""

from __future__ import annotations

from typing import Any

from game_core.algorithms import ClueAlgorithm, GuessAlgorithm

from clue_eval.benchmark.runner import BenchmarkRunner
from clue_eval.operatives.factory import OperativeKind
from clue_eval.scenarios.runner import ScenarioRunner
from clue_eval.suite.types import ClueTest, TestSuite


class SuiteRunner:
    """Execute a :class:`TestSuite` using the model-agnostic scenario harness."""

    def __init__(
        self,
        algorithm: ClueAlgorithm,
        *,
        guess_algorithm: GuessAlgorithm | None = None,
        operative_condition: OperativeKind | None = None,
    ) -> None:
        self._scenario_runner = ScenarioRunner(
            algorithm,
            guess_algorithm=guess_algorithm,
            operative_condition=operative_condition,
        )

    def run_test(self, test: ClueTest) -> dict[str, Any]:
        result = self._scenario_runner.run(test.scenario)
        result["test_id"] = test.id
        result["description"] = test.description
        result["tags"] = sorted(test.tags)
        return result

    def run_suite(self, suite: TestSuite) -> list[dict[str, Any]]:
        scenarios = [test.scenario for test in suite.tests]
        benchmark = BenchmarkRunner(self._scenario_runner)
        print(f"Suite {suite.name!r}: {suite.description}")
        results = benchmark.run_suite(scenarios)
        for result, test in zip(results, suite.tests, strict=True):
            result["test_id"] = test.id
            result["description"] = test.description
            result["tags"] = sorted(test.tags)
        return results
