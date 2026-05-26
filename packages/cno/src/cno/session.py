"""High-level spymaster session for codenames.game."""

from __future__ import annotations

import logging

from cno_sdk.client import CNOClient
from cno_sdk.state import TeamColor, pick_friendly_words

logger = logging.getLogger(__name__)

HARDCODED_CLUE_WORD = "PINEAPPLE"
HARDCODED_SELECTED_WORDS = ["HEAVEN", "BULB", "CHICK"]
HARDCODED_COUNT = 3


class SpymasterSession:
    """Join a room as spymaster, wait for turn, and give a hardcoded test clue."""

    def __init__(
        self,
        room: str,
        team: TeamColor,
        nickname: str = "SpymasterBot",
    ) -> None:
        self.room = room
        self.team = team
        self.nickname = nickname
        self.client = CNOClient(room_slug=room, nickname=nickname)

    async def run(self) -> None:
        logger.info("Connecting to room %s as %s...", self.room, self.nickname)
        await self.client.connect()
        logger.info(
            "Connected (player_id=%s). Joining %s spymasters...",
            self.client.player_id,
            self.team,
        )

        await self.client.join_team(self.team, "spymasters")
        logger.info("Joined team. Waiting for spymaster turn...")

        state = await self.client.wait_for_spymaster_turn(self.team)
        selected = pick_friendly_words(
            state,
            self.team,
            HARDCODED_SELECTED_WORDS,
            HARDCODED_COUNT,
        )
        logger.info(
            "Our turn. Giving clue %s / %d (%s)",
            HARDCODED_CLUE_WORD,
            len(selected),
            ", ".join(selected),
        )
        await self.client.give_clue(HARDCODED_CLUE_WORD, selected)
        logger.info("Clue submitted successfully.")

    async def close(self) -> None:
        await self.client.close()
