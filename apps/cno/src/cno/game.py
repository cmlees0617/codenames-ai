"""Run full codenames.game matches with multiple bots."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from cno.bots.operative import CNOOperativeBot
from cno.bots.spymaster import AutoCNOSpymasterBot
from cno_sdk.client import CNOClient
from cno_sdk.room import create_room
from cno_sdk.state import TeamColor
from cluegen.algorithms import (
    CluegenClueAlgorithm,
    ScriptedClueAlgorithm,
    ScriptedGuessAlgorithm,
)
from game_core.types import Clue

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FullGameResult:
    room: str
    url: str
    winner: object | None


def _build_scripted_guesses(state, team: TeamColor) -> list[str | None]:
    """Guess friendly words first, then pass when no guesses remain."""
    friendly = [
        card.word
        for card in state.grid
        if card.color == team and not card.revealed
    ]
    return [word for word in friendly] + [None]


def _scripted_clue_for_team(state, team: TeamColor) -> Clue:
    targets = tuple(
        card.word
        for card in state.grid
        if card.color == team and not card.revealed
    )[:3]
    return Clue(word="TEST", count=len(targets), intended_targets=targets)


async def run_full_game(
    *,
    shutdown: asyncio.Event | None = None,
    use_cluegen: bool = False,
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

    grid_state = host.state

    if use_cluegen:
        clue_algo_red = clue_algo_blue = CluegenClueAlgorithm()
    else:
        clue_algo_red = ScriptedClueAlgorithm([_scripted_clue_for_team(grid_state, "red")])
        clue_algo_blue = ScriptedClueAlgorithm([_scripted_clue_for_team(grid_state, "blue")])

    red_sm = AutoCNOSpymasterBot(
        "red",
        clue_algo_red,
        room=room,
        nickname="RedSpymaster",
        shutdown=shutdown,
        client=red_sm_client,
    )
    blue_sm = AutoCNOSpymasterBot(
        "blue",
        clue_algo_blue,
        room=room,
        nickname="BlueSpymaster",
        shutdown=shutdown,
        client=blue_sm_client,
    )
    red_op = CNOOperativeBot(
        "red",
        ScriptedGuessAlgorithm(_build_scripted_guesses(grid_state, "red")),
        room=room,
        nickname="RedOperative",
        shutdown=shutdown,
        client=red_op_client,
    )
    blue_op = CNOOperativeBot(
        "blue",
        ScriptedGuessAlgorithm(_build_scripted_guesses(grid_state, "blue")),
        room=room,
        nickname="BlueOperative",
        shutdown=shutdown,
        client=blue_op_client,
    )

    players = [red_sm, blue_sm, red_op, blue_op]
    tasks = [asyncio.create_task(player.play()) for player in players]

    try:
        await asyncio.wait_for(asyncio.gather(*tasks), timeout=game_timeout)
    finally:
        winner = host.state.gameover
        for player in players:
            await player.close()
        await host.leave()

    return FullGameResult(
        room=room,
        url=f"https://codenames.game/r/{room}",
        winner=winner,
    )
