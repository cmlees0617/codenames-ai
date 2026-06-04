#!/usr/bin/env python3
"""
Generate the standard 5000-board benchmark set for clue-eval.

Writes ``packages/clue-eval/data/standard_boards_5000.json`` with boards ordered
from least to most difficult (mean blue/red difficulty). End users can load this
file and split into train/test subsets as needed.

Usage (from repository root)::

    uv sync --all-packages
    uv run python packages/clue-eval/examples/generate_standard_board_set.py

Requires ``data/glove-wiki-gigaword-300.npz`` (see ``uv run --extra embeddings clue-eval-embed``).

Generation may take several minutes depending on hardware.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from clue_eval.boards import BoardFactory
from clue_eval.embeddings.store import EmbeddingStore
from clue_eval.paths import default_embeddings_path, default_standard_boards_path

STANDARD_BOARD_COUNT = 5000
DEFAULT_BETA = 2.0
DEFAULT_CANDIDATE_MULTIPLIER = 100


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate the standard clue-eval benchmark board set (JSON).",
    )
    parser.add_argument(
        "-n",
        "--count",
        type=int,
        default=STANDARD_BOARD_COUNT,
        help=f"Number of boards (default: {STANDARD_BOARD_COUNT})",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output JSON path (default: data/standard_boards_5000.json)",
    )
    parser.add_argument("--beta", type=float, default=DEFAULT_BETA, help="Assassin weight")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed for layouts")
    parser.add_argument(
        "--candidate-multiplier",
        type=int,
        default=DEFAULT_CANDIDATE_MULTIPLIER,
        help="Sample count = n * this before uniform difficulty selection",
    )
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable the candidate-scoring progress bar",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    embeddings_path = default_embeddings_path()
    if not embeddings_path.exists():
        print(
            f"Missing embeddings: {embeddings_path}\n"
            "Run: uv run --extra embeddings clue-eval-embed",
            file=sys.stderr,
        )
        return 1

    output_path = args.output or default_standard_boards_path()
    print(f"Loading embeddings from {embeddings_path}...")
    store = EmbeddingStore.load(embeddings_path)

    print(
        f"Generating {args.count} boards (beta={args.beta}, "
        f"candidate_multiplier={args.candidate_multiplier}, seed={args.seed})..."
    )
    start = time.perf_counter()
    BoardFactory.generate_and_save_uniform_difficulty_boards(
        args.count,
        store,
        output_path,
        beta=args.beta,
        candidate_multiplier=args.candidate_multiplier,
        seed=args.seed,
        sort_by_difficulty=True,
        show_progress=not args.no_progress,
    )
    elapsed = time.perf_counter() - start

    print(f"Wrote {args.count} boards to {output_path} ({elapsed:.1f}s)")
    print("Boards are sorted easiest → hardest; split into train/test in your own code.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
