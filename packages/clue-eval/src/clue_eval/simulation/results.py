"""Load, save, and summarize spymaster simulation benchmarks."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from clue_eval.operatives.factory import OperativeKind
from clue_eval.paths import package_data_dir
from clue_eval.simulation.game import SimulatedGameResult


@dataclass(frozen=True, slots=True)
class SimulationBatchResult:
    """Aggregate outcome of simulating every board in a benchmark set."""

    spymaster_name: str
    operative_kind: OperativeKind
    games: tuple[SimulatedGameResult, ...]

    def summary(self) -> dict[str, int]:
        counts = {"win": 0, "loss": 0, "abort": 0}
        for game in self.games:
            counts[game.outcome] += 1
        return counts

    def as_dict(self) -> dict[str, Any]:
        return {
            "spymaster_name": self.spymaster_name,
            "operative_kind": self.operative_kind,
            "board_count": len(self.games),
            "summary": self.summary(),
            "games": [game.as_dict() for game in self.games],
        }


def default_results_dir() -> Path:
    return package_data_dir() / "results"


def results_path_for_model(
    spymaster_name: str,
    operative_kind: OperativeKind,
    *,
    sample_size: int | None = None,
) -> Path:
    """
    ``data/results/{spymaster}_{operative}.json``.

    Sample runs use ``..._{operative}_sample{N}.json`` so they do not overwrite full benchmarks.
    """
    suffix = f"_sample{sample_size}" if sample_size is not None else ""
    return default_results_dir() / f"{spymaster_name}_{operative_kind}{suffix}.json"


def save_simulation_results(
    batch: SimulationBatchResult,
    path: Path | None = None,
) -> Path:
    """Write batch results to JSON (creates parent directories)."""
    output = path or results_path_for_model(batch.spymaster_name, batch.operative_kind)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(batch.as_dict(), indent=2), encoding="utf-8")
    return output


def load_simulation_results(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)
