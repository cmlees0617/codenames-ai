"""CNO operative player bot."""

from __future__ import annotations

import asyncio
import logging

from cno_sdk.client import CNOClient
from cno_sdk.state import TeamColor, is_operative_turn
from game_core.algorithms import GuessAlgorithm

from cno_bots.bots import _cno_player as cno
from cno_bots.views import to_operative_view

logger = logging.getLogger(__name__)


class CNOOperativeBot:
    """Play operative on codenames.game using a GuessAlgorithm."""

    def __init__(
        self,
        team: TeamColor,
        guess_algorithm: GuessAlgorithm,
        *,
        room: str,
        nickname: str = "OperativeBot",
        shutdown: asyncio.Event | None = None,
        client: CNOClient | None = None,
    ) -> None:
        self.team = team
        self.guess_algorithm = guess_algorithm
        self.room = room
        self.nickname = nickname
        self.shutdown = shutdown
        self.client = client

    async def play(self) -> str:
        if self.client is None:
            self.client = CNOClient(room_slug=self.room, nickname=self.nickname)
            logger.info("Connecting to room %s as %s operative...", self.room, self.nickname)
            await self.client.connect()
        assert self.client is not None
        assert self.client.player_id is not None
        await cno.join_if_needed(self.client, self.team, "operatives")
        logger.info("Joined %s operatives. Waiting for turns...", self.team)

        while self.client.state.gameover is None:
            cno.check_shutdown(self.shutdown)
            if not await cno.wait_operative_turn(self.client, self.team, self.shutdown):
                break
            if self.client.state.gameover is not None:
                break

            while (
                self.client.state.gameover is None
                and is_operative_turn(
                    self.client.state,
                    self.client.player_id,
                    self.team,
                )
            ):
                cno.check_shutdown(self.shutdown)
                view = to_operative_view(self.client.state, self.team)
                action = await asyncio.to_thread(self.guess_algorithm.guess_word, view)

                if action.pass_turn:
                    logger.info("Ending guessing.")
                    await self.client.end_guessing()
                    break

                assert action.word is not None
                logger.info("Guessing %s", action.word)
                await self.client.guess_card(action.word)
                await asyncio.sleep(0.2)

                if not is_operative_turn(
                    self.client.state,
                    self.client.player_id,
                    self.team,
                ):
                    break

        return self.room

    async def close(self) -> None:
        if self.client is not None:
            await self.client.leave()
