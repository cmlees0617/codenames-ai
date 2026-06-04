"""Async player loops (one role per protocol)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class SpymasterPlayer(Protocol):
    async def play(self) -> str:
        """Connect, join, and play spymaster turns until game over."""

    async def close(self) -> None:
        """Leave the room and release resources."""


@runtime_checkable
class OperativePlayer(Protocol):
    async def play(self) -> str:
        """Connect, join, and play operative turns until game over."""

    async def close(self) -> None:
        """Leave the room and release resources."""
