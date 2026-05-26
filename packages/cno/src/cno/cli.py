"""CLI entry point for codenames.game spymaster bot."""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys

from cno.session import SpymasterSession
from cno_sdk.state import Role, TeamColor

ROLE_CHOICES = {
    "red-spymaster": ("red", "spymasters"),
    "blue-spymaster": ("blue", "spymasters"),
    "red-operative": ("red", "operatives"),
    "blue-operative": ("blue", "operatives"),
}


def parse_role(role: str) -> tuple[TeamColor, Role]:
    key = role.lower().replace("_", "-")
    if key not in ROLE_CHOICES:
        valid = ", ".join(sorted(ROLE_CHOICES))
        raise argparse.ArgumentTypeError(
            f"Invalid role {role!r}. Expected one of: {valid}"
        )
    return ROLE_CHOICES[key]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cno",
        description="Join a codenames.game room as spymaster and give a test clue.",
    )
    parser.add_argument("room", help="Room slug from the URL, e.g. halok-jonah")
    parser.add_argument(
        "role",
        type=parse_role,
        help="Team role, e.g. red-spymaster or blue-spymaster",
    )
    parser.add_argument(
        "--nickname",
        default="SpymasterBot",
        help="Display name in the room (default: SpymasterBot)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    return parser


async def _async_main(args: argparse.Namespace) -> int:
    team, role = args.role
    if role != "spymasters":
        logging.error("v1 only supports spymaster roles")
        return 1

    session = SpymasterSession(room=args.room, team=team, nickname=args.nickname)
    try:
        await session.run()
        return 0
    finally:
        await session.close()


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )
    raise SystemExit(asyncio.run(_async_main(args)))


if __name__ == "__main__":
    main()
