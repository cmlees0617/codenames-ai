"""Game backend protocol (not implemented for CNO yet).

``CNOSpymasterBot`` / ``CNOOperativeBot`` talk to ``CNOClient`` directly today.
When a second Codenames implementation exists, extract connect / wait / submit
behind a ``GameBackend`` adapter and keep player bots backend-agnostic.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from game_core.types import Clue, GuessAction, Role, TeamColor
from game_core.views import OperativeView, SpymasterView


@runtime_checkable
class GameBackend(Protocol):
    """Async transport for one Codenames room (future multi-backend support)."""

    async def connect(self) -> None: ...

    async def join(self, team: TeamColor, role: Role) -> None: ...

    async def wait_for_spymaster_turn(self, team: TeamColor) -> SpymasterView: ...

    async def wait_for_operative_turn(self, team: TeamColor) -> OperativeView: ...

    async def submit_clue(self, team: TeamColor, clue: Clue) -> None: ...

    async def submit_guess(self, team: TeamColor, action: GuessAction) -> None: ...

    async def disconnect(self) -> None: ...

    @property
    def gameover(self) -> str | None: ...
