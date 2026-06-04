"""Run evaluation scenarios against any :class:`~game_core.algorithms.ClueAlgorithm`."""

from __future__ import annotations

from typing import Any

from game_core.algorithms import ClueAlgorithm
from game_core.types import Clue

from clue_eval.boards.views import board_layout_to_spymaster_view
from clue_eval.scenarios.types import Scenario


def _clue_to_dict(clue: Clue) -> dict[str, Any]:
    return {
        "word": clue.word,
        "count": clue.count,
        "intended_targets": list(clue.intended_targets),
    }


class ScenarioRunner:
    """Execute scenarios using any implementation of ``ClueAlgorithm``."""

    def __init__(self, algorithm: ClueAlgorithm) -> None:
        self.algorithm = algorithm

    def run(self, scenario: Scenario) -> dict[str, Any]:
        """Rank clues for ``scenario`` and return structured results."""
        view = board_layout_to_spymaster_view(scenario.board, team=scenario.team)
        clues = self.algorithm.rank_clues(view, limit=scenario.clue_limit)
        top = clues[0] if clues else None

        targets_covered = list(top.intended_targets) if top else []
        result: dict[str, Any] = {
            "name": scenario.name,
            "team": scenario.team,
            "generated_clue": top.word if top else None,
            "targets_covered": targets_covered,
            "top_clue": _clue_to_dict(top) if top else None,
            "clues": [_clue_to_dict(clue) for clue in clues],
            "metadata": dict(scenario.metadata),
        }

        if scenario.expected_targets is not None:
            covered = {word.upper() for word in targets_covered}
            expected = {word.upper() for word in scenario.expected_targets}
            result["pass"] = expected <= covered
            result["expected_targets"] = sorted(expected)
            result["missing_targets"] = sorted(expected - covered)
        else:
            result["pass"] = None

        return result
