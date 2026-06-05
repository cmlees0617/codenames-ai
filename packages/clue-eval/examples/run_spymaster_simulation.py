#!/usr/bin/env python3
"""
Run the 5000-board spymaster benchmark against operative test conditions.

Full run (default): 3 × 5000 = 15,000 games, three JSON files.

Debug / smoke (first N boards, one operative)::

    uv run python packages/clue-eval/examples/run_spymaster_simulation.py \\
        --cluegen --operative static_embedding --sample 25

Usage (from repository root)::

    uv sync --all-packages
    uv sync --package clue-eval --extra embeddings   # static / softmax operatives
    uv run python packages/clue-eval/examples/run_spymaster_simulation.py --cluegen
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

from clue_eval.operatives.factory import OPERATIVE_KINDS, SELECTABLE_OPERATIVE_KINDS
from clue_eval.simulation import (
    SpymasterSimulationRunner,
    results_path_for_model,
    run_spymaster_benchmark_all_operatives,
)
from clue_eval.simulation.naming import resolve_spymaster_name


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Simulate spymaster benchmark games. "
            "Default: all three operatives on all boards. "
            "Use --operative and --sample for faster debug runs."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Operatives: "
            + ", ".join(SELECTABLE_OPERATIVE_KINDS)
            + "\n\nExamples:\n"
            "  %(prog)s --cluegen --operative static_embedding --sample 50\n"
            "  %(prog)s --cluegen --operative cluegen_embedding --sample 100\n"
            "  %(prog)s --stub --sample 10\n"
        ),
    )
    parser.add_argument(
        "--operative",
        choices=SELECTABLE_OPERATIVE_KINDS,
        default=None,
        metavar="KIND",
        help=(
            "Run one operative test condition only "
            f"({', '.join(SELECTABLE_OPERATIVE_KINDS)}). Default: all three "
            f"benchmark operatives ({', '.join(OPERATIVE_KINDS)})."
        ),
    )
    parser.add_argument(
        "-n",
        "--sample",
        "--limit",
        type=int,
        default=None,
        dest="sample",
        metavar="N",
        help="Use only the first N boards from the benchmark set (file order)",
    )
    parser.add_argument(
        "--spymaster-module",
        type=str,
        default=None,
        help="Import path to ClueAlgorithm class, e.g. mypkg.spymaster:MyAlgorithm",
    )
    parser.add_argument(
        "--stub",
        action="store_true",
        help="Use clue_eval.demos.stub_algorithm.StubClueAlgorithm",
    )
    parser.add_argument(
        "--cluegen",
        action="store_true",
        help="Use cluegen.algorithms.CluegenClueAlgorithm (example embedding spymaster)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output JSON path (default: data/results/{spymaster}_{operative}[_sampleN].json)",
    )
    parser.add_argument(
        "--boards",
        type=Path,
        default=None,
        help="Board JSON path (default: standard_boards_5000.json)",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--no-progress", action="store_true")
    return parser


def load_spymaster(module_path: str):
    if ":" not in module_path:
        raise ValueError("Use module.path:ClassName for --spymaster-module")
    module_name, class_name = module_path.split(":", 1)
    module = importlib.import_module(module_name)
    cls = getattr(module, class_name)
    return cls()


def _print_run_plan(
    *,
    spymaster_name: str,
    board_count: int | None,
    sample: int | None,
    operative: str | None,
) -> None:
    boards_label = str(sample) if sample is not None else "5000 (full set)"
    if operative is None:
        conditions = f"all three operatives ({', '.join(OPERATIVE_KINDS)})"
        games = (sample or 5000) * 3
    else:
        conditions = operative
        games = sample or 5000
    print(
        f"Spymaster {spymaster_name!r}: {boards_label} boards × {conditions} "
        f"→ {games} games"
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.sample is not None and args.sample < 1:
        print("--sample must be >= 1", file=sys.stderr)
        return 1

    if args.stub:
        from clue_eval.demos.stub_algorithm import StubClueAlgorithm

        spymaster = StubClueAlgorithm()
    elif args.cluegen:
        from cluegen.algorithms import CluegenClueAlgorithm

        spymaster = CluegenClueAlgorithm()
    elif args.spymaster_module:
        spymaster = load_spymaster(args.spymaster_module)
    else:
        print("Provide --stub, --cluegen, or --spymaster-module", file=sys.stderr)
        return 1

    spymaster_name = resolve_spymaster_name(spymaster)
    _print_run_plan(
        spymaster_name=spymaster_name,
        board_count=args.sample,
        sample=args.sample,
        operative=args.operative,
    )

    show_progress = not args.no_progress

    if args.operative is not None:
        runner = SpymasterSimulationRunner(
            spymaster,
            args.operative,
            boards_path=args.boards,
            board_limit=args.sample,
            seed=args.seed,
            show_progress=show_progress,
        )
        output = args.output or results_path_for_model(
            spymaster_name,
            args.operative,
            sample_size=args.sample,
        )
        path = runner.run_and_save(output)
        print(f"Wrote {len(runner.boards)} game results to {path}")
        return 0

    operative_kinds = OPERATIVE_KINDS
    paths = run_spymaster_benchmark_all_operatives(
        spymaster,
        boards_path=args.boards,
        board_limit=args.sample,
        seed=args.seed,
        show_progress=show_progress,
        operative_kinds=operative_kinds,
    )
    if paths:
        print(f"Wrote {len(paths)} results files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
