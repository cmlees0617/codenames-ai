"""Role-scoped game snapshots."""

from __future__ import annotations

from dataclasses import dataclass, field

from game_core.types import TeamColor, TileColor


@dataclass(frozen=True)
class SpymasterBoardCard:
    word: str
    color: TileColor
    revealed: bool


@dataclass(frozen=True)
class SpymasterView:
    team: TeamColor
    board: tuple[SpymasterBoardCard, ...]
    active_team: TeamColor | None = None
    gameover: str | None = None


@dataclass(frozen=True)
class BoardTileView:
    """Operative-visible tile (no hidden team color on unrevealed cards)."""

    word: str
    revealed: bool
    color: TileColor | None = None


@dataclass(frozen=True)
class ClueHistoryEntry:
    word: str
    count: int
    team: TeamColor | None = None


@dataclass(frozen=True)
class OperativeView:
    team: TeamColor
    board: tuple[BoardTileView, ...]
    current_clue: ClueHistoryEntry | None = None
    guesses_remaining: int = 0
    clue_history: tuple[ClueHistoryEntry, ...] = field(default_factory=tuple)
    gameover: str | None = None
