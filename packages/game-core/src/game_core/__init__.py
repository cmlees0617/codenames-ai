"""Game-agnostic Codenames types and protocols."""

from game_core.algorithms import ClueAlgorithm, GuessAlgorithm
from game_core.players import OperativePlayer, SpymasterPlayer
from game_core.types import Clue, GuessAction, TeamColor, TileColor
from game_core.views import BoardTileView, OperativeView, SpymasterBoardCard, SpymasterView

__all__ = [
    "BoardTileView",
    "Clue",
    "ClueAlgorithm",
    "GuessAction",
    "GuessAlgorithm",
    "OperativePlayer",
    "OperativeView",
    "SpymasterBoardCard",
    "SpymasterPlayer",
    "SpymasterView",
    "TeamColor",
    "TileColor",
]
