"""Live integration checks against codenames.game (requires network)."""

from __future__ import annotations

import pytest

from cno_sdk.client import CNOClient
from cno_sdk.room import create_room
from cno_sdk.state import is_seated

pytestmark = pytest.mark.integration


async def _cleanup(client: CNOClient) -> None:
    client._log_session = False
    await client.leave()


@pytest.mark.asyncio
async def test_live_create_room_and_join_red_spymaster():
    created = await create_room(nickname="SDK-Create-Room-Bot")
    try:
        client = created.client
        assert created.slug
        assert client.player_id is not None
        assert client.match_id != "default"

        await client.join_team("red", "spymasters")
        assert is_seated(client.state, client.player_id, "red", "spymasters")
    finally:
        await _cleanup(created.client)


@pytest.mark.asyncio
async def test_live_connect_existing_room():
    client = CNOClient(room_slug="bonik-jorop", nickname="SDK-Integration-Bot")
    try:
        await client.connect()
        assert client.player_id is not None
    finally:
        await _cleanup(client)


@pytest.mark.asyncio
async def test_live_give_clue_wire_format():
    created = await create_room(nickname="SDK-GiveClue-Bot")
    try:
        client = created.client
        await client.join_team("red", "spymasters")
        await client.give_clue("PINEAPPLE", ["HEAVEN", "BULB", "CHICK"])
    finally:
        await _cleanup(created.client)
