"""Live integration checks against codenames.game (requires network)."""

from __future__ import annotations

import pytest

from cno_sdk.client import CNOClient
from cno_sdk.state import is_seated

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_live_connect_and_join_red_spymaster():
    nickname = "SDK-Integration-Bot"
    client = CNOClient(room_slug="halok-jonah", nickname=nickname)
    try:
        await client.connect()
        assert client.player_id is not None
        assert client.match_id != "default"

        await client.join_team("red", "spymasters")
        assert is_seated(client.state, client.player_id, "red", "spymasters")
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_live_give_clue_wire_format():
    client = CNOClient(room_slug="halok-jonah", nickname="SDK-GiveClue-Bot")
    try:
        await client.connect()
        await client.join_team("red", "spymasters")
        await client.give_clue("PINEAPPLE", ["HEAVEN", "BULB", "CHICK"])
    finally:
        await client.close()
