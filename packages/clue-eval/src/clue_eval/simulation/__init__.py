"""Full-game spymaster test pipeline (experimental; likely to be reworked)."""

from clue_eval.simulation.game import GameOutcome, SimulatedGameResult, simulate_game
from clue_eval.simulation.naming import resolve_spymaster_name, sanitize_model_filename
from clue_eval.simulation.results import (
    SimulationBatchResult,
    default_results_dir,
    results_path_for_model,
    save_simulation_results,
)
from clue_eval.simulation.runner import (
    SpymasterSimulationRunner,
    run_spymaster_benchmark_all_operatives,
)
from clue_eval.simulation.state import BoardGameState, spymaster_team_for_board

__all__ = [
    "BoardGameState",
    "GameOutcome",
    "SimulatedGameResult",
    "SimulationBatchResult",
    "SpymasterSimulationRunner",
    "run_spymaster_benchmark_all_operatives",
    "default_results_dir",
    "resolve_spymaster_name",
    "results_path_for_model",
    "sanitize_model_filename",
    "save_simulation_results",
    "simulate_game",
    "spymaster_team_for_board",
]
