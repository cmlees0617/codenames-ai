"""Async player loops (one role per protocol)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class SpymasterPlayer(Protocol):
    """Runs the spymaster role until the game ends."""

    async def play(self) -> str:
        """Connect, join, give clues each turn. Returns the room slug."""

    async def close(self) -> None:
        """Leave the room and release resources."""


@runtime_checkable
class OperativePlayer(Protocol):
    """Runs the operative role until the game ends."""

    async def play(self) -> str:
        """Connect, join, guess each operative phase. Returns the room slug."""

    async def close(self) -> None:
        """Leave the room and release resources."""
