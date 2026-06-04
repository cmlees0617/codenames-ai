"""Scenario definitions for clue evaluation."""

from __future__ import annotations

from dataclasses import dataclass, field

from game_core.types import TeamColor

from clue_eval.boards.types import BoardLayout


@dataclass(frozen=True, slots=True)
class Scenario:
    """
    One offline clue-generation test case (model-agnostic).

    The runner calls ``ClueAlgorithm.rank_clues`` on a :class:`~game_core.views.SpymasterView`
    derived from ``board``. Fixture keys ``blues`` / ``reds`` are board colors, not
    the playing team; set ``team`` to the spymaster's side.

    When ``expected_targets`` is set, ``pass`` is true if every expected word appears
    in the top-ranked clue's ``intended_targets``.
    """

    name: str
    board: BoardLayout
    team: TeamColor = "blue"
    clue_limit: int = 10
    expected_targets: frozenset[str] | None = None
    metadata: dict[str, object] = field(default_factory=dict)
