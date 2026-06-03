"""Neutral domain types for Codenames."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

TeamColor = Literal["red", "blue"]
TileColor = Literal["red", "blue", "civilian", "assassin"]


@dataclass(frozen=True)
class Clue:
    word: str
    count: int
    intended_targets: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "word", self.word.upper())
        if self.count < 0:
            raise ValueError("count must be non-negative")


@dataclass(frozen=True)
class GuessAction:
    word: str | None = None
    pass_turn: bool = False

    def __post_init__(self) -> None:
        if self.pass_turn and self.word is not None:
            raise ValueError("pass_turn cannot be combined with a word")
        if not self.pass_turn and self.word is None:
            raise ValueError("must pass_turn or provide a word")
        if self.word is not None:
            object.__setattr__(self, "word", self.word.upper())

    @classmethod
    def guess(cls, word: str) -> GuessAction:
        return cls(word=word, pass_turn=False)

    @classmethod
    def end_turn(cls) -> GuessAction:
        return cls(pass_turn=True)
