"""Build operative views from offline board layouts."""

from __future__ import annotations

from game_core.types import TeamColor
from game_core.views import BoardTileView, ClueHistoryEntry, OperativeView

from clue_eval.boards.types import BoardLayout


def iter_board_words(board: BoardLayout) -> list[str]:
    """All words on a layout in stable order."""
    return (
        list(board["blues"])
        + list(board["reds"])
        + list(board["civilians"])
        + list(board["assassins"])
    )


def board_layout_to_operative_view(
    board: BoardLayout,
    *,
    team: TeamColor,
    clue_word: str,
    clue_count: int,
    guesses_remaining: int | None = None,
) -> OperativeView:
    """Operative-visible snapshot for one clue (unrevealed tiles, no hidden colors)."""
    remaining = guesses_remaining if guesses_remaining is not None else clue_count
    tiles = tuple(
        BoardTileView(word=word.upper(), revealed=False) for word in iter_board_words(board)
    )
    clue = ClueHistoryEntry(word=clue_word.upper(), count=clue_count, team=team)
    return OperativeView(
        team=team,
        board=tiles,
        current_clue=clue,
        guesses_remaining=remaining,
    )


def apply_guess(state: OperativeView, word: str) -> OperativeView:
    """Mark a guessed tile revealed and decrement remaining guesses."""
    upper = word.upper()
    updated_board = tuple(
        BoardTileView(
            word=tile.word,
            revealed=tile.revealed or tile.word == upper,
            color=tile.color,
        )
        for tile in state.board
    )
    remaining = max(0, state.guesses_remaining - 1)
    return OperativeView(
        team=state.team,
        board=updated_board,
        current_clue=state.current_clue,
        guesses_remaining=remaining,
        clue_history=state.clue_history,
        gameover=state.gameover,
    )
