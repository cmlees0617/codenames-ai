"""Thin CLI: parse arguments, collect interactive input, start a cno-bots player."""

from __future__ import annotations

import argparse
import asyncio
import logging

from cno_bots.factory import PlayerBuildOptions, build_player
from cno_bots.runner import ShutdownController, run_player
from cno_sdk.state import Role, TeamColor

from cno.interactive import prompt_interactive, prompt_select_clue
from cno.roles import default_nickname, parse_role


def parse_role_arg(role: str) -> tuple[TeamColor, Role]:
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


def _player_options(args: argparse.Namespace) -> PlayerBuildOptions:
    team, role = args.role
    return PlayerBuildOptions(
        team=team,
        role=role,
        room=args.room,
        nickname=args.nickname or default_nickname(team, role),
        random_operative=args.random_operative,
        select_clue=prompt_select_clue if args.interactive else None,
    )


async def _async_main(args: argparse.Namespace) -> int:
    _normalize_args(args)
    error = _validate_args(args)
    if error:
        logging.error(error)
        return 1

    try:
        player = build_player(_player_options(args))
    except ValueError as exc:
        logging.error("%s", exc)
        return 1

    return await run_player(player, shutdown=ShutdownController())


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
