"""Room creation helpers for codenames.game."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cno_sdk.client import CNOClient


@dataclass(frozen=True)
class CreatedRoom:
    """A freshly created codenames.game room."""

    slug: str
    url: str
    client: CNOClient

    @property
    def match_id(self) -> str:
        return self.client.match_id

    @property
    def player_id(self) -> str:
        if self.client.player_id is None:
            raise RuntimeError("player_id is not assigned")
        return self.client.player_id


async def create_room(
    nickname: str = "TestHost",
    *,
    credentials: str | None = None,
) -> CreatedRoom:
    """Create a new room on the lobby server and return a connected client."""
    from cno_sdk.client import CNOClient

    client = await CNOClient.create_room(
        nickname=nickname,
        credentials=credentials,
    )
    slug = client.room_slug
    return CreatedRoom(
        slug=slug,
        url=f"https://codenames.game/r/{slug}",
        client=client,
    )


async def close_room(created: CreatedRoom) -> None:
    """Leave team and disconnect from a created room."""
    await created.client.leave()
