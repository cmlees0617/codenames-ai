"""Async player loops (one role per protocol)."""

from __future__ import annotations

from typing import Protocol


class SpymasterPlayer(Protocol):
    async def play(self) -> str | None:
        """Connect, join, and play spymaster turns until game over. Returns room slug."""


class OperativePlayer(Protocol):
    async def play(self) -> str | None:
        """Connect, join, and play operative turns until game over. Returns room slug."""
