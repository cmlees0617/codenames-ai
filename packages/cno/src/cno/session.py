"""High-level bot sessions for codenames.game."""

from __future__ import annotations

import asyncio
import logging
import random

from cno.clue_engine import ClueEngine, GeneratedClue
from cno_sdk.client import CNOClient, GameEnded
from cno_sdk.room import create_room
from cno_sdk.state import (
    GameState,
    TeamColor,
    friendly_unrevealed,
    is_operative_turn,
    is_seated,
    unrevealed_cards,
)

logger = logging.getLogger(__name__)


class SpymasterSession:
    """Join as spymaster, give clues every turn, stay until game over."""

    def __init__(
        self,
        team: TeamColor,
        *,
        room: str | None = None,
        nickname: str = "SpymasterBot",
        create_room_if_needed: bool = False,
        shutdown: asyncio.Event | None = None,
        clue_engine: ClueEngine | None = None,
    ) -> None:
        self.team = team
        self.room = room
        self.nickname = nickname
        self.create_room_if_needed = create_room_if_needed or room is None
        self.shutdown = shutdown
        self.clue_engine = clue_engine or ClueEngine()
        self.client: CNOClient | None = None

    async def run(self) -> str:
        if self.client is None:
            if self.create_room_if_needed:
                created = await create_room(nickname=self.nickname)
                self.client = created.client
                self.room = created.slug
                logger.info("Created room %s (%s)", self.room, created.url)
            else:
                if not self.room:
                    raise ValueError("room is required unless create_room_if_needed=True")
                self.client = CNOClient(room_slug=self.room, nickname=self.nickname)
                logger.info("Connecting to room %s as %s...", self.room, self.nickname)
                await self.client.connect()
        else:
            self.room = self.room or self.client.room_slug

        assert self.client is not None
        if self.create_room_if_needed and self.client._sio.connected:
            logger.info(
                "Connected (player_id=%s). Joining %s spymasters...",
                self.client.player_id,
                self.team,
            )
        elif not self.create_room_if_needed:
            logger.info(
                "Connected (player_id=%s). Joining %s spymasters...",
                self.client.player_id,
                self.team,
            )

        assert self.client is not None
        if self.client.player_id is not None and not is_seated(
            self.client.state,
            self.client.player_id,
            self.team,
            "spymasters",
        ):
            await self.client.join_team(self.team, "spymasters")
        logger.info("Joined team. Waiting for turns...")

        while self.client.state.gameover is None:
            if self.shutdown and self.shutdown.is_set():
                raise asyncio.CancelledError("Shutdown requested")

            try:
                state = await self.client.wait_for_spymaster_turn(
                    self.team,
                    shutdown=self.shutdown,
                )
            except GameEnded as exc:
                logger.info("Game ended (%s).", exc.winner)
                break
            except asyncio.CancelledError:
                raise

            if state.gameover is not None:
                logger.info("Game ended (%s).", state.gameover)
                break

            if not friendly_unrevealed(state, self.team):
                continue

            clue = await self._generate_clue(state)
            logger.info(
                "Our turn. Giving clue %s / %d (%s)",
                clue.word,
                len(clue.targets),
                ", ".join(clue.targets),
            )
            await self.client.give_clue(clue.word, clue.targets)

        return self.room

    async def _generate_clue(self, state: GameState) -> GeneratedClue:
        try:
            return await asyncio.to_thread(
                self.clue_engine.generate,
                state,
                self.team,
            )
        except Exception as exc:
            logger.warning("Clue generation failed (%s); using fallback clue.", exc)
            fallback_targets = [card.word for card in friendly_unrevealed(state, self.team)][:3]
            return GeneratedClue(word="HINT", targets=fallback_targets)

    async def close(self) -> None:
        if self.client is not None:
            await self.client.leave()


class OperativeSession:
    """Join as operative and guess random unrevealed tiles on each turn."""

    def __init__(
        self,
        team: TeamColor,
        *,
        room: str,
        nickname: str = "OperativeBot",
        shutdown: asyncio.Event | None = None,
    ) -> None:
        self.team = team
        self.room = room
        self.nickname = nickname
        self.shutdown = shutdown
        self.client: CNOClient | None = None

    async def run(self) -> str:
        if self.client is None:
            self.client = CNOClient(room_slug=self.room, nickname=self.nickname)
            logger.info("Connecting to room %s as %s operative...", self.room, self.nickname)
            await self.client.connect()
        assert self.client.player_id is not None
        if not is_seated(
            self.client.state,
            self.client.player_id,
            self.team,
            "operatives",
        ):
            await self.client.join_team(self.team, "operatives")
        logger.info("Joined %s operatives. Waiting for turns...", self.team)

        assert self.client.player_id is not None
        while self.client.state.gameover is None:
            if self.shutdown and self.shutdown.is_set():
                raise asyncio.CancelledError("Shutdown requested")

            try:
                state = await self.client.wait_for_operative_turn(
                    self.team,
                    shutdown=self.shutdown,
                )
            except GameEnded as exc:
                logger.info("Game ended (%s).", exc.winner)
                break
            except asyncio.CancelledError:
                raise

            if state.gameover is not None:
                logger.info("Game ended (%s).", state.gameover)
                break

            while (
                self.client.state.gameover is None
                and is_operative_turn(
                    self.client.state,
                    self.client.player_id,
                    self.team,
                )
            ):
                if self.shutdown and self.shutdown.is_set():
                    raise asyncio.CancelledError("Shutdown requested")

                cards = unrevealed_cards(self.client.state)
                if not cards:
                    break
                word = random.choice(cards).word
                logger.info("Guessing %s", word)
                await self.client.guess_card(word)
                await asyncio.sleep(0.2)

        return self.room

    async def close(self) -> None:
        if self.client is not None:
            await self.client.leave()
