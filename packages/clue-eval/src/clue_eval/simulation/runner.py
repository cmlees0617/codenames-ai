"""Run full-game simulations across the standard 5000-board benchmark."""

from __future__ import annotations

import random
from pathlib import Path
from typing import TYPE_CHECKING

from tqdm import tqdm

from clue_eval.boards.io import load_standard_boards
from clue_eval.operatives.factory import OPERATIVE_KINDS, OperativeKind, create_operative_algorithm
from clue_eval.simulation.game import SimulatedGameResult, simulate_game
from clue_eval.simulation.naming import resolve_spymaster_name
from clue_eval.simulation.results import (
    SimulationBatchResult,
    results_path_for_model,
    save_simulation_results,
)

if TYPE_CHECKING:
    from game_core.algorithms import ClueAlgorithm, GuessAlgorithm


class SpymasterSimulationRunner:
    """
    Simulate full games on the standard board set for one spymaster + operative pair.

    Boards are loaded into memory once. Each game uses the test spymaster on the
    team with more words (see :func:`~clue_eval.simulation.state.spymaster_team_for_board`),
    paired with the chosen operative on that same team.
    """

    def __init__(
        self,
        spymaster: ClueAlgorithm,
        operative_kind: OperativeKind,
        *,
        boards: list | None = None,
        boards_path: Path | None = None,
        board_limit: int | None = None,
        sample_size: int | None = None,
        guess_algorithm: GuessAlgorithm | None = None,
        seed: int | None = None,
        show_progress: bool = True,
    ) -> None:
        self.spymaster = spymaster
        self.spymaster_name = resolve_spymaster_name(spymaster)
        self.operative_kind = operative_kind
        self._guess_algorithm = guess_algorithm
        self._rng = random.Random(seed)
        self.show_progress = show_progress
        self.sample_size = sample_size if sample_size is not None else board_limit

        if boards is not None:
            self.boards = boards
            if board_limit is not None:
                self.boards = self.boards[:board_limit]
        else:
            self.boards = load_standard_boards(boards_path, limit=board_limit)

    def run_all(self) -> SimulationBatchResult:
        """Simulate every loaded board and return aggregated results."""
        games: list[SimulatedGameResult] = []
        iterator = self.boards
        if self.show_progress:
            iterator = tqdm(
                self.boards,
                desc=f"{self.spymaster_name} vs {self.operative_kind}",
                unit="game",
            )

        for board in iterator:
            per_game_rng = random.Random(self._rng.randint(0, 2**31 - 1))
            operative = self._guess_algorithm or create_operative_algorithm(self.operative_kind)
            games.append(
                simulate_game(
                    board,
                    self.spymaster,
                    operative,
                    rng=per_game_rng,
                )
            )

        return SimulationBatchResult(
            spymaster_name=self.spymaster_name,
            operative_kind=self.operative_kind,
            games=tuple(games),
        )

    def run_and_save(self, output_path: Path | None = None) -> Path:
        """Run all games and write JSON results."""
        batch = self.run_all()
        destination = output_path or results_path_for_model(
            self.spymaster_name,
            self.operative_kind,
            sample_size=self.sample_size,
        )
        return save_simulation_results(batch, destination)


def run_spymaster_benchmark_all_operatives(
    spymaster: ClueAlgorithm,
    *,
    boards: list | None = None,
    boards_path: Path | None = None,
    board_limit: int | None = None,
    seed: int | None = 42,
    show_progress: bool = True,
    operative_kinds: tuple[OperativeKind, ...] = OPERATIVE_KINDS,
) -> list[Path]:
    """
    Run the full benchmark for every operative test condition (3 × 5000 games by default).

    Loads boards once, then simulates all games for each operative and writes one JSON
    file per operative: ``{spymaster_name}_{operative_kind}.json``.
    """
    spymaster_name = resolve_spymaster_name(spymaster)
    if boards is not None:
        loaded_boards = boards[:board_limit] if board_limit is not None else boards
    else:
        loaded_boards = load_standard_boards(boards_path, limit=board_limit)

    output_paths: list[Path] = []
    condition_iterator: tuple[OperativeKind, ...] | tqdm = operative_kinds
    if show_progress:
        condition_iterator = tqdm(
            operative_kinds,
            desc=f"{spymaster_name}: operative conditions",
            unit="condition",
        )

    for operative_kind in condition_iterator:
        runner = SpymasterSimulationRunner(
            spymaster,
            operative_kind,
            boards=loaded_boards,
            sample_size=board_limit,
            seed=seed,
            show_progress=show_progress,
        )
        output_paths.append(runner.run_and_save())

    total_games = len(loaded_boards) * len(operative_kinds)
    print(
        f"Finished {total_games} games for spymaster {spymaster_name!r} "
        f"({len(loaded_boards)} boards × {len(operative_kinds)} operatives)."
    )
    for path in output_paths:
        print(f"  {path}")
    return output_paths
