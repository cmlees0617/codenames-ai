"""CLI entry point for codenames.game bots."""

from __future__ import annotations

import argparse
import asyncio
import logging

from cno.bots.operative import CNOOperativeBot
from cno.bots.spymaster import AutoCNOSpymasterBot, InteractiveCNOSpymasterBot
from cno.interactive import prompt_interactive
from cno.roles import default_nickname, parse_role
from cno.shutdown import ShutdownController
from cluegen.algorithms import (
    CluegenClueAlgorithm,
    EmbeddingGuessAlgorithm,
    RandomGuessAlgorithm,
)


def parse_role_arg(role: str):
    try:
        return parse_role(role)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cno",
        description="Join a codenames.game room as a spymaster or operative bot.",
    )
    parser.add_argument(
        "room",
        nargs="?",
        help="Room slug from the URL, e.g. halok-jonah",
    )
    parser.add_argument(
        "role",
        nargs="?",
        type=parse_role_arg,
        help="Team role, e.g. red-spymaster, blue-operative",
    )
    parser.add_argument(
        "--nickname",
        default=None,
        help="Display name in the room (defaults to role-based name)",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Spymaster only: pick from top-ranked clues instead of auto-selecting",
    )
    parser.add_argument(
        "--random-operative",
        action="store_true",
        help="Operative only: guess random tiles instead of embedding similarity",
    )
    return parser


def _build_player(args: argparse.Namespace, shutdown: asyncio.Event):
    team, role = args.role
    nickname = args.nickname or default_nickname(team, role)

    if role == "spymasters":
        clue_algorithm = CluegenClueAlgorithm()
        if args.interactive:
            return InteractiveCNOSpymasterBot(
                team,
                clue_algorithm,
                room=args.room,
                nickname=nickname,
                shutdown=shutdown,
            )
        return AutoCNOSpymasterBot(
            team,
            clue_algorithm,
            room=args.room,
            nickname=nickname,
            shutdown=shutdown,
        )
    if role == "operatives":
        guess_algorithm = (
            RandomGuessAlgorithm()
            if args.random_operative
            else EmbeddingGuessAlgorithm()
        )
        return CNOOperativeBot(
            team,
            guess_algorithm,
            room=args.room,
            nickname=nickname,
            shutdown=shutdown,
        )
    raise ValueError(f"Unsupported role {role}")


def _validate_args(args: argparse.Namespace) -> str | None:
    if not args.room:
        return "Provide a room slug from the URL, e.g. halok-jonah"
    return None


def _normalize_args(args: argparse.Namespace) -> None:
    if args.role is not None:
        return
    if not args.room:
        return
    args.role = parse_role(args.room)
    args.room = None


async def _async_main(args: argparse.Namespace) -> int:
    _normalize_args(args)
    error = _validate_args(args)
    if error:
        logging.error(error)
        return 1

    shutdown = ShutdownController()
    try:
        player = _build_player(args, shutdown.event)
    except ValueError as exc:
        logging.error("%s", exc)
        return 1

    run_task = asyncio.create_task(player.play())
    shutdown.install(
        asyncio.get_running_loop(),
        player.close,
        run_task=run_task,
    )

    try:
        await run_task
        return 0
    except asyncio.CancelledError:
        logging.info("Interrupted.")
        return 130
    finally:
        await shutdown.close(player.close)


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    if argv is None:
        import sys

        argv = sys.argv[1:]

    if not argv:
        args = prompt_interactive()
    else:
        args = parser.parse_args(argv)
        _normalize_args(args)

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(levelname)s %(message)s",
    )
    raise SystemExit(asyncio.run(_async_main(args)))


if __name__ == "__main__":
    main()
