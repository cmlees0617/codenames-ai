"""Board layout types for offline evaluation."""

from __future__ import annotations

from typing import NotRequired, TypedDict


class BoardLayout(TypedDict):
    """Standard 25-card Codenames layout keyed by team color."""

    blues: list[str]
    reds: list[str]
    civilians: list[str]
    assassins: list[str]


class FixtureBoard(BoardLayout, total=False):
    """Fixed board for offline evaluation."""

    id: NotRequired[int]
