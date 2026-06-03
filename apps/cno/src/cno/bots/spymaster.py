"""CNO spymaster player bots."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable

import questionary

from cno.bots import _cno_player as cno
from cno.views import to_spymaster_view
from cno_sdk.client import CNOClient
from cno_sdk.state import TeamColor, friendly_unrevealed
from game_core.algorithms import ClueAlgorithm
from game_core.types import Clue

logger = logging.getLogger(__name__)


class CNOSpymasterBot:
    """Play spymaster on codenames.game using a ClueAlgorithm and selection strategy."""

    def __init__(
        self,
        team: TeamColor,
        clue_algorithm: ClueAlgorithm,
        *,
        room: str | None = None,
        nickname: str = "SpymasterBot",
        create_room_if_needed: bool = False,
        shutdown: asyncio.Event | None = None,
        client: CNOClient | None = None,
        select_clue: Callable[[list[Clue]], Clue | None] | None = None,
        rank_limit: int = 10,
    ) -> None:
        self.team = team
        self.clue_algorithm = clue_algorithm
        self.room = room
        self.nickname = nickname
        self.create_room_if_needed = create_room_if_needed or room is None
        self.shutdown = shutdown
        self.client = client
        self._select_clue = select_clue or (lambda clues: clues[0] if clues else None)
        self.rank_limit = rank_limit

    async def play(self) -> str:
        self.client, self.room = await cno.ensure_connected(
            client=self.client,
            room=self.room,
            nickname=self.nickname,
            create_room_if_needed=self.create_room_if_needed,
        )
        assert self.client is not None
        await cno.join_if_needed(self.client, self.team, "spymasters")
        logger.info("Joined %s spymasters. Waiting for turns...", self.team)

        while self.client.state.gameover is None:
            cno.check_shutdown(self.shutdown)
            if not await cno.wait_spymaster_turn(self.client, self.team, self.shutdown):
                break
            if self.client.state.gameover is not None:
                break
            if not friendly_unrevealed(self.client.state, self.team):
                continue

            clue = await self._pick_clue()
            if clue is None:
                clue = self._fallback_clue()

            logger.info(
                "Our turn. Giving clue %s / %d (%s)",
                clue.word,
                clue.count,
                ", ".join(clue.intended_targets),
            )
            targets = list(clue.intended_targets) or [
                card.word for card in friendly_unrevealed(self.client.state, self.team)
            ][: clue.count or 3]
            await self.client.give_clue(clue.word, targets)

        return self.room

    async def _pick_clue(self) -> Clue | None:
        view = to_spymaster_view(self.client.state, self.team)  # type: ignore[union-attr]
        try:
            clues = await asyncio.to_thread(
                self.clue_algorithm.rank_clues,
                view,
                limit=self.rank_limit,
            )
        except Exception as exc:
            logger.warning("Clue ranking failed (%s).", exc)
            return None
        return self._select_clue(clues)

    def _fallback_clue(self) -> Clue:
        assert self.client is not None
        targets = tuple(
            card.word for card in friendly_unrevealed(self.client.state, self.team)
        )[:3]
        return Clue(word="HINT", count=len(targets), intended_targets=targets)

    async def close(self) -> None:
        if self.client is not None:
            await self.client.leave()


class AutoCNOSpymasterBot(CNOSpymasterBot):
    """Automatically play the top-ranked clue."""

    def __init__(self, team: TeamColor, clue_algorithm: ClueAlgorithm, **kwargs) -> None:
        super().__init__(
            team,
            clue_algorithm,
            select_clue=lambda clues: clues[0] if clues else None,
            **kwargs,
        )


class InteractiveCNOSpymasterBot(CNOSpymasterBot):
    """Let a human pick from the top-ranked clues."""

    def __init__(self, team: TeamColor, clue_algorithm: ClueAlgorithm, **kwargs) -> None:
        super().__init__(
            team,
            clue_algorithm,
            select_clue=InteractiveCNOSpymasterBot._prompt_select,
            rank_limit=10,
            **kwargs,
        )

    @staticmethod
    def _prompt_select(clues: list[Clue]) -> Clue | None:
        if not clues:
            return None
        choices = [
            questionary.Choice(
                title=f"{clue.word} / {clue.count} → {', '.join(clue.intended_targets)}",
                value=clue,
            )
            for clue in clues
        ]
        return questionary.select(
            "Select a clue:",
            choices=choices,
        ).ask()
