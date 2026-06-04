"""Run collections of evaluation scenarios and print aggregate stats."""

from __future__ import annotations

import time
from typing import Any

from clue_eval.scenarios.runner import ScenarioRunner
from clue_eval.scenarios.types import Scenario


class BenchmarkRunner:
    """Runs performance and quality benchmarks across multiple scenarios."""

    def __init__(self, runner: ScenarioRunner) -> None:
        self.runner = runner

    def run_suite(self, scenarios: list[Scenario]) -> list[dict[str, Any]]:
        """Run each scenario and return per-scenario result dicts."""
        results: list[dict[str, Any]] = []
        print(f"Running benchmark suite with {len(scenarios)} scenarios...")

        for scenario in scenarios:
            start = time.perf_counter()
            result = self.runner.run(scenario)
            elapsed = time.perf_counter() - start
            result["time_sec"] = elapsed
            results.append(result)

            passed = result.get("pass")
            if passed is False:
                status = "FAIL"
            elif passed is True:
                status = "PASS"
            else:
                status = "RUN"
            clue_word = result.get("generated_clue")
            target_count = len(result.get("targets_covered") or [])
            print(
                f"[{status}] {scenario.name}: {clue_word!r} "
                f"targets={target_count} ({elapsed:.2f}s)"
            )

        self._print_summary(results)
        return results

    def _print_summary(self, results: list[dict[str, Any]]) -> None:
        total = len(results)
        if total == 0:
            return

        avg_time = sum(r["time_sec"] for r in results) / total
        graded = [r for r in results if r.get("pass") is not None]
        passed = [r for r in graded if r.get("pass") is True]

        print("\n--- Benchmark Summary ---")
        print(f"Scenarios: {total}")
        print(f"Average Time: {avg_time:.3f}s")
        if graded:
            accuracy = len(passed) / len(graded)
            print(f"Accuracy (Ground Truth): {len(passed)}/{len(graded)} ({accuracy:.1%})")
        print("-------------------------\n")
