"""Predefined clue tests and model-agnostic evaluation harness."""

from clue_eval.benchmark.runner import BenchmarkRunner
from clue_eval.boards.factory import BoardFactory
from clue_eval.boards.io import load_boards_from_json
from clue_eval.boards.types import BoardLayout
from clue_eval.boards.views import board_layout_to_spymaster_view
from clue_eval.clues import (
    ClueLegalityResult,
    is_legal_clue,
    validate_clue_legality,
)
from clue_eval.operatives import (
    OPERATIVE_KINDS,
    OperativeKind,
    create_operative_algorithm,
)
from clue_eval.paths import package_data_dir
from clue_eval.scenarios.runner import ScenarioRunner
from clue_eval.scenarios.types import Scenario
from clue_eval.simulation import SpymasterSimulationRunner, run_spymaster_benchmark_all_operatives
from clue_eval.suite import ClueTest, SuiteRunner, TestSuite, all_suites, default_suite

__all__ = [
    "OPERATIVE_KINDS",
    "OperativeKind",
    "BenchmarkRunner",
    "BoardFactory",
    "BoardLayout",
    "ClueLegalityResult",
    "ClueTest",
    "Scenario",
    "ScenarioRunner",
    "SpymasterSimulationRunner",
    "run_spymaster_benchmark_all_operatives",
    "create_operative_algorithm",
    "is_legal_clue",
    "validate_clue_legality",
    "SuiteRunner",
    "TestSuite",
    "all_suites",
    "board_layout_to_spymaster_view",
    "default_suite",
    "load_boards_from_json",
    "package_data_dir",
]
