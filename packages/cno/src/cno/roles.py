"""Role parsing helpers for the cno CLI."""

from __future__ import annotations

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
        raise ValueError(f"Invalid role {role!r}. Expected one of: {valid}")
    return ROLE_CHOICES[key]


def default_nickname(team: TeamColor, role: Role) -> str:
    label = role[:-1] if role.endswith("s") else role
    return f"{team.title()}{label.title()}Bot"
