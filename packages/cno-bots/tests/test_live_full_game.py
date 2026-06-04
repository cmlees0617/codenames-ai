"""Live full-game integration test."""

from __future__ import annotations

import pytest
from cno_bots.game import run_full_game

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_live_full_game_with_four_bots() -> None:
    result = await run_full_game(game_timeout=180.0)
    assert result.room
    assert result.winner is not None
    winner = (
        result.winner
        if isinstance(result.winner, str)
        else result.winner.get("team")
    )
    assert winner in ("red", "blue")
