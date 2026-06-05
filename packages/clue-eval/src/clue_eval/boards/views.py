"""Convert fixture board layouts into :class:`~game_core.views.SpymasterView`."""

from __future__ import annotations

from game_core.types import TeamColor, TileColor
from game_core.views import SpymasterBoardCard, SpymasterView

from clue_eval.boards.types import BoardLayout


def board_layout_to_spymaster_view(
    board: BoardLayout,
    *,
    team: TeamColor,
) -> SpymasterView:
    """Build a spymaster view from a fixture layout (unrevealed cards)."""

    def cards(color: TileColor, words: list[str]) -> tuple[SpymasterBoardCard, ...]:
        return tuple(
            SpymasterBoardCard(word=word, color=color, revealed=False) for word in words
        )

    all_cards = (
        cards("blue", board["blues"])
        + cards("red", board["reds"])
        + cards("civilian", board["civilians"])
        + cards("assassin", board["assassins"])
    )
    return SpymasterView(team=team, board=all_cards)
