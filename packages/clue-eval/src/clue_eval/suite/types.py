"""Predefined clue-evaluation tests (model-agnostic)."""

from __future__ import annotations

from dataclasses import dataclass, field

from clue_eval.scenarios.types import Scenario


@dataclass(frozen=True, slots=True)
class ClueTest:
    """
    One entry in the repo's predefined evaluation catalog.

    ``scenario`` supplies board state and optional ground-truth targets.
    Additional assertions (legality, assassin distance, etc.) can be added here later.
    """

    id: str
    scenario: Scenario
    description: str = ""
    tags: frozenset[str] = field(default_factory=frozenset)


@dataclass(frozen=True, slots=True)
class TestSuite:
    """Named collection of :class:`ClueTest` cases."""

    name: str
    tests: tuple[ClueTest, ...]
    description: str = ""
