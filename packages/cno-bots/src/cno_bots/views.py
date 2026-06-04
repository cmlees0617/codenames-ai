"""Map cno-sdk GameState to game-core role views (CNO adapter layer)."""

from __future__ import annotations

from cno_sdk.state import CardColor, GameState, TeamColor, card_color_to_tile, parse_clues
from game_core.types import TileColor
from game_core.views import (
    BoardTileView,
    ClueHistoryEntry,
    OperativeView,
    SpymasterBoardCard,
    SpymasterView,
)


def _tile_color(card_color: CardColor) -> TileColor:
    return card_color_to_tile(card_color)


def to_spymaster_view(state: GameState, team: TeamColor) -> SpymasterView:
    board = tuple(
        SpymasterBoardCard(
            word=card.word,
            color=_tile_color(card.color),
            revealed=card.revealed,
        )
        for card in state.grid
    )
    return SpymasterView(
        team=team,
        board=board,
        active_team=state.active_team,
        gameover=state.gameover,
    )


def to_operative_view(state: GameState, team: TeamColor) -> OperativeView:
    board = tuple(
        BoardTileView(
            word=card.word,
            revealed=card.revealed,
            color=_tile_color(card.color) if card.revealed else None,
        )
        for card in state.grid
    )
    clues = parse_clues(state.log)
    history = tuple(
        ClueHistoryEntry(word=c.word, count=c.count, team=c.team) for c in clues
    )
    current_entry = None
    if state.active_team == team and clues:
        current = clues[-1]
        current_entry = ClueHistoryEntry(
            word=current.word,
            count=current.count,
            team=current.team,
        )

    return OperativeView(
        team=team,
        board=board,
        current_clue=current_entry,
        guesses_remaining=state.guess_limit or 0,
        clue_history=history,
        gameover=state.gameover,
    )
