"""Run evaluation scenarios against any :class:`~game_core.algorithms.ClueAlgorithm`."""

from __future__ import annotations

from typing import Any

from game_core.algorithms import ClueAlgorithm, GuessAlgorithm
from game_core.types import Clue

from clue_eval.boards.views import board_layout_to_spymaster_view
from clue_eval.clues.legality import validate_clue_legality, visible_words_from_board
from clue_eval.operatives.simulation import evaluate_operative_turn
from clue_eval.scenarios.types import Scenario


def _clue_to_dict(clue: Clue) -> dict[str, Any]:
    return {
        "word": clue.word,
        "count": clue.count,
        "intended_targets": list(clue.intended_targets),
    }


class ScenarioRunner:
    """Execute scenarios using any implementation of ``ClueAlgorithm``."""

    def __init__(
        self,
        algorithm: ClueAlgorithm,
        *,
        guess_algorithm: GuessAlgorithm | None = None,
        operative_condition: str | None = None,
    ) -> None:
        self.algorithm = algorithm
        if guess_algorithm is not None and operative_condition is not None:
            raise ValueError("Pass guess_algorithm or operative_condition, not both.")
        self.operative_condition = operative_condition
        if operative_condition is not None:
            from clue_eval.operatives.factory import create_operative_algorithm

            guess_algorithm = create_operative_algorithm(operative_condition)  # type: ignore[arg-type]
        self.guess_algorithm = guess_algorithm

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

        if top is not None:
            legality = validate_clue_legality(
                top.word,
                top.count,
                visible_words_from_board(scenario.board),
            )
            result["clue_legality"] = legality.as_dict()

        if self.guess_algorithm is not None and top is not None and top.count > 0:
            operative = evaluate_operative_turn(
                scenario.board,
                scenario.team,
                top,
                self.guess_algorithm,
            )
            result["operative"] = operative
            if self.operative_condition is not None:
                result["operative_condition"] = self.operative_condition

        return result
