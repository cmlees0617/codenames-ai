"""Predefined test catalog (extend this module as new cases are added)."""

from __future__ import annotations

from clue_eval.boards.io import load_boards_from_json
from clue_eval.paths import default_test_boards_path
from clue_eval.scenarios.types import Scenario
from clue_eval.suite.types import ClueTest, TestSuite


def _fixture_tests() -> tuple[ClueTest, ...]:
    """Boards from ``data/test_boards.json`` — baseline layout coverage."""
    boards = load_boards_from_json(default_test_boards_path())
    tests: list[ClueTest] = []
    for index, board in enumerate(boards):
        test_id = str(board.get("id", index))
        clue_test_id = f"fixture-{test_id}"
        tests.append(
            ClueTest(
                id=clue_test_id,
                description=f"Fixture board {test_id}",
                scenario=Scenario(name=clue_test_id, board=board),
                tags=frozenset({"fixture"}),
            )
        )
    return tuple(tests)


def default_suite() -> TestSuite:
    """
    Default predefined suite shipped with the repo.

    Add new :class:`ClueTest` entries here (or load from JSON under ``data/``) as the
    catalog grows. Algorithms are graded only against these tests, not against each other.
    """
    return TestSuite(
        name="default",
        description="Starter catalog: fixture boards (more cases TBD).",
        tests=_fixture_tests(),
    )


def all_suites() -> tuple[TestSuite, ...]:
    """Registered suites. Extend when adding named catalogs."""
    return (default_suite(),)
