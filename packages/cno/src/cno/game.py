"""Run full codenames.game matches with multiple bots."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from cno.session import OperativeSession, SpymasterSession
from cno_sdk.client import CNOClient
from cno_sdk.room import create_room

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FullGameResult:
    room: str
    url: str
    winner: object | None


async def run_full_game(
    *,
    shutdown: asyncio.Event | None = None,
    start_timeout: float = 30.0,
    game_timeout: float = 600.0,
) -> FullGameResult:
    """Seat four bots, start a match, and play until game over."""
    created = await create_room(nickname="GameHost")
    room = created.slug
    host = created.client
    host._log_session = False

    async def connect_bot(name: str) -> CNOClient:
        client = CNOClient(room_slug=room, nickname=name)
        client._log_session = False
        await client.connect()
        return client

    red_sm_client = await connect_bot("RedSpymaster")
    blue_sm_client = await connect_bot("BlueSpymaster")
    red_op_client = await connect_bot("RedOperative")
    blue_op_client = await connect_bot("BlueOperative")

    await red_sm_client.join_team("red", "spymasters")
    await blue_sm_client.join_team("blue", "spymasters")
    await red_op_client.join_team("red", "operatives")
    await blue_op_client.join_team("blue", "operatives")

    await host.start_match()
    logger.info("Match started in room %s", room)

    for client in (red_sm_client, blue_sm_client, red_op_client, blue_op_client):
        client._synced.clear()
        await client.request_sync()
        await asyncio.wait_for(client._synced.wait(), timeout=10)

    red_sm = SpymasterSession("red", room=room, nickname="RedSpymaster", shutdown=shutdown)
    red_sm.client = red_sm_client
    blue_sm = SpymasterSession("blue", room=room, nickname="BlueSpymaster", shutdown=shutdown)
    blue_sm.client = blue_sm_client
    red_op = OperativeSession("red", room=room, nickname="RedOperative", shutdown=shutdown)
    red_op.client = red_op_client
    blue_op = OperativeSession("blue", room=room, nickname="BlueOperative", shutdown=shutdown)
    blue_op.client = blue_op_client

    sessions = [red_sm, blue_sm, red_op, blue_op]
    tasks = [asyncio.create_task(session.run()) for session in sessions]

    try:
        await asyncio.wait_for(asyncio.gather(*tasks), timeout=game_timeout)
    finally:
        winner = host.state.gameover
        for session in sessions:
            await session.close()
        await host.leave()

    return FullGameResult(
        room=room,
        url=f"https://codenames.game/r/{room}",
        winner=winner,
    )
