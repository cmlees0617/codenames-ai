"""Run the predefined test suite against a ClueAlgorithm."""

from __future__ import annotations

import argparse

from clue_eval.demos.stub_algorithm import StubClueAlgorithm
from clue_eval.suite import SuiteRunner, default_suite


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the repo's predefined clue tests against a ClueAlgorithm. "
            "Pass your own algorithm via the Python API (SuiteRunner)."
        ),
    )
    parser.add_argument(
        "--stub",
        action="store_true",
        help="Use the built-in stub algorithm (smoke test, no ML)",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    if not args.stub:
        print(
            "Provide a ClueAlgorithm in code, e.g.\n"
            "  SuiteRunner(MyClueAlgorithm()).run_suite(default_suite())\n"
            "Use --stub for a no-ML smoke run."
        )
        raise SystemExit(0)

    SuiteRunner(StubClueAlgorithm()).run_suite(default_suite())


if __name__ == "__main__":
    main()
