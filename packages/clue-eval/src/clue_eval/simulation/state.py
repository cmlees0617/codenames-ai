"""Mutable board state for offline full-game simulation."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from game_core.types import TeamColor, TileColor
from game_core.views import (
    BoardTileView,
    ClueHistoryEntry,
    OperativeView,
    SpymasterBoardCard,
    SpymasterView,
)

from clue_eval.boards.types import BoardLayout
from clue_eval.operatives.views import iter_board_words


def test_spymaster_team(board: BoardLayout) -> TeamColor:
    """Return the team color that has more words on ``board`` (not always blue)."""
    blue_count = len(board["blues"])
    red_count = len(board["reds"])
    if blue_count > red_count:
        return "blue"
    if red_count > blue_count:
        return "red"
    raise ValueError(
        f"Cannot assign test spymaster: blue and red both have {blue_count} words."
    )


def opponent_team(team: TeamColor) -> TeamColor:
    return "red" if team == "blue" else "blue"


def tile_color_for_team(team: TeamColor) -> TileColor:
    return team


@dataclass
class BoardGameState:
    """Hidden-color board with reveal tracking."""

    word_colors: dict[str, TileColor]
    revealed: set[str] = field(default_factory=set)
    word_order: tuple[str, ...] = ()

    @classmethod
    def from_layout(cls, board: BoardLayout) -> BoardGameState:
        colors: dict[str, TileColor] = {}
        for word in board["blues"]:
            colors[word.upper()] = "blue"
        for word in board["reds"]:
            colors[word.upper()] = "red"
        for word in board["civilians"]:
            colors[word.upper()] = "civilian"
        for word in board["assassins"]:
            colors[word.upper()] = "assassin"
        order = tuple(word.upper() for word in iter_board_words(board))
        return cls(word_colors=colors, revealed=set(), word_order=order)

    def color_of(self, word: str) -> TileColor:
        return self.word_colors[word.upper()]

    def is_revealed(self, word: str) -> bool:
        return word.upper() in self.revealed

    def reveal(self, word: str) -> TileColor:
        upper = word.upper()
        if upper not in self.word_colors:
            raise KeyError(f"Unknown board word: {word!r}")
        self.revealed.add(upper)
        return self.word_colors[upper]

    def unrevealed_words(self) -> list[str]:
        return [word for word in self.word_order if word not in self.revealed]

    def unrevealed_team_words(self, team: TeamColor) -> list[str]:
        target_color = tile_color_for_team(team)
        return [
            word
            for word in self.unrevealed_words()
            if self.word_colors[word] == target_color
        ]

    def team_words_remaining(self, team: TeamColor) -> int:
        return len(self.unrevealed_team_words(team))

    def spymaster_view(self, team: TeamColor) -> SpymasterView:
        cards = tuple(
            SpymasterBoardCard(
                word=word,
                color=self.word_colors[word],
                revealed=word in self.revealed,
            )
            for word in self.word_order
        )
        return SpymasterView(team=team, board=cards)

    def operative_view(
        self,
        team: TeamColor,
        *,
        clue_word: str,
        clue_count: int,
        guesses_remaining: int,
    ) -> OperativeView:
        tiles = tuple(
            BoardTileView(
                word=word,
                revealed=word in self.revealed,
                color=self.word_colors[word] if word in self.revealed else None,
            )
            for word in self.word_order
        )
        clue = ClueHistoryEntry(word=clue_word.upper(), count=clue_count, team=team)
        return OperativeView(
            team=team,
            board=tiles,
            current_clue=clue,
            guesses_remaining=guesses_remaining,
        )

    def reveal_random_opponent_word(self, test_team: TeamColor, rng: random.Random) -> str | None:
        """Reveal one random unrevealed word belonging to the opposing team."""
        other = opponent_team(test_team)
        candidates = self.unrevealed_team_words(other)
        if not candidates:
            return None
        chosen = rng.choice(candidates)
        self.reveal(chosen)
        return chosen
