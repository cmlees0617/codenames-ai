"""Interactive prompts for the cno CLI (terminal UI only)."""

from __future__ import annotations

import argparse
import sys
from typing import cast

import questionary
from game_core.types import Clue
from questionary import Style

from cno.roles import default_nickname, parse_role

_MENU_STYLE = Style([
    ("qmark", "fg:cyan bold"),
    ("question", "bold"),
    ("pointer", "fg:cyan bold"),
    ("highlighted", "fg:cyan bold"),
    ("answer", "fg:cyan"),
])


def _select(title: str, options: list[str]) -> str:
    choice = questionary.select(
        title,
        choices=options,
        style=_MENU_STYLE,
        use_indicator=True,
    ).ask()
    if choice is None:
        raise SystemExit(0)
    return cast(str, choice)


def _text(title: str, *, default: str = "") -> str:
    value = questionary.text(
        title,
        default=default,
        style=_MENU_STYLE,
    ).ask()
    if value is None:
        raise SystemExit(0)
    return cast(str, value).strip()


def prompt_select_clue(clues: list[Clue]) -> Clue | None:
    """Human-in-the-loop clue picker (used as ``select_clue`` for spymaster bots)."""
    if not clues:
        return None
    choices = [
        questionary.Choice(
            title=f"{clue.word} / {clue.count} → {', '.join(clue.intended_targets)}",
            value=clue,
        )
        for clue in clues
    ]
    return cast(Clue | None, questionary.select(
        "Select a clue:",
        choices=choices,
    ).ask())


def prompt_interactive() -> argparse.Namespace:
    """Collect run settings from the terminal."""
    print("Codenames Online — Bot\n")

    role_key = _select(
        "Team role",
        [
            "red-spymaster",
            "blue-spymaster",
            "red-operative",
            "blue-operative",
        ],
    )
    team, role = parse_role(role_key)

    while True:
        room = _text("Room slug (from the URL, e.g. halok-jonah)")
        if room:
            break
        print("Room slug is required.", file=sys.stderr)

    nickname_default = default_nickname(team, role)
    nickname = _text("Nickname", default=nickname_default) or nickname_default

    print()
    return argparse.Namespace(
        room=room,
        role=(team, role),
        nickname=nickname,
        interactive=False,
        random_operative=False,
    )
