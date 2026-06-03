"""Shared helpers for CNO player bots."""

from __future__ import annotations

import asyncio
import logging

from cno_sdk.client import CNOClient, GameEnded
from cno_sdk.room import create_room
from cno_sdk.state import Role, TeamColor, is_seated

logger = logging.getLogger(__name__)


async def ensure_connected(
    *,
    client: CNOClient | None,
    room: str | None,
    nickname: str,
    create_room_if_needed: bool,
) -> tuple[CNOClient, str]:
    if client is not None:
        slug = room or client.room_slug
        if slug is None:
            raise ValueError("room slug unknown for pre-connected client")
        return client, slug

    if create_room_if_needed:
        created = await create_room(nickname=nickname)
        logger.info("Created room %s (%s)", created.slug, created.url)
        return created.client, created.slug

    if not room:
        raise ValueError("room is required unless create_room_if_needed=True")
    new_client = CNOClient(room_slug=room, nickname=nickname)
    logger.info("Connecting to room %s as %s...", room, nickname)
    await new_client.connect()
    return new_client, room


def check_shutdown(shutdown: asyncio.Event | None) -> None:
    if shutdown and shutdown.is_set():
        raise asyncio.CancelledError("Shutdown requested")


async def join_if_needed(
    client: CNOClient,
    team: TeamColor,
    role: Role,
) -> None:
    if client.player_id is None:
        raise RuntimeError("client not connected")
    if not is_seated(client.state, client.player_id, team, role):
        await client.join_team(team, role)


async def wait_spymaster_turn(
    client: CNOClient,
    team: TeamColor,
    shutdown: asyncio.Event | None,
) -> bool:
    """Wait for spymaster turn. Returns False if game ended."""
    try:
        state = await client.wait_for_spymaster_turn(team, shutdown=shutdown)
    except GameEnded as exc:
        logger.info("Game ended (%s).", exc.winner)
        return False
    return state.gameover is None


async def wait_operative_turn(
    client: CNOClient,
    team: TeamColor,
    shutdown: asyncio.Event | None,
) -> bool:
    try:
        state = await client.wait_for_operative_turn(team, shutdown=shutdown)
    except GameEnded as exc:
        logger.info("Game ended (%s).", exc.winner)
        return False
    return state.gameover is None
