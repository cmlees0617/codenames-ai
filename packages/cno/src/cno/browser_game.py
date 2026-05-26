"""Run a match with spymaster bots and browser-based operatives."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from cno.session import SpymasterSession
from cno_sdk.client import CNOClient
from cno_sdk.room import create_room

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SpymasterGameHandle:
    room: str
    url: str
    host: CNOClient
    red_sm: SpymasterSession
    blue_sm: SpymasterSession


async def start_spymaster_game(
    *,
    shutdown: asyncio.Event | None = None,
) -> SpymasterGameHandle:
    """Create a room, seat two spymaster bots, and start the match."""
    created = await create_room(nickname="GameHost")
    room = created.slug
    host = created.client
    host._log_session = False

    async def connect(name: str) -> CNOClient:
        client = CNOClient(room_slug=room, nickname=name)
        client._log_session = False
        await client.connect()
        return client

    red_client = await connect("RedSpymaster")
    blue_client = await connect("BlueSpymaster")
    await red_client.join_team("red", "spymasters")
    await blue_client.join_team("blue", "spymasters")

    await host.start_match()
    for client in (red_client, blue_client):
        await client.request_sync()
        await asyncio.wait_for(client._synced.wait(), timeout=10)

    red_sm = SpymasterSession("red", room=room, nickname="RedSpymaster", shutdown=shutdown)
    red_sm.client = red_client
    blue_sm = SpymasterSession("blue", room=room, nickname="BlueSpymaster", shutdown=shutdown)
    blue_sm.client = blue_client

    return SpymasterGameHandle(
        room=room,
        url=f"https://codenames.game/r/{room}",
        host=host,
        red_sm=red_sm,
        blue_sm=blue_sm,
    )


async def run_spymaster_bots(
    handle: SpymasterGameHandle,
    *,
    game_timeout: float = 600.0,
) -> object | None:
    """Run spymaster bot loops until the game ends."""
    tasks = [
        asyncio.create_task(handle.red_sm.run()),
        asyncio.create_task(handle.blue_sm.run()),
    ]
    try:
        await asyncio.wait_for(asyncio.gather(*tasks), timeout=game_timeout)
    finally:
        for session in (handle.red_sm, handle.blue_sm):
            await session.close()
        winner = handle.host.state.gameover
        await handle.host.leave()
        return winner
