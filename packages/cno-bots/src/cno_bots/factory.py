"""Construct CNO player bots from role and algorithm options."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from cluegen.algorithms import (
    CluegenClueAlgorithm,
    EmbeddingGuessAlgorithm,
    RandomGuessAlgorithm,
)
from cno_sdk.state import Role, TeamColor
from game_core.algorithms import ClueAlgorithm, GuessAlgorithm
from game_core.players import OperativePlayer, SpymasterPlayer
from game_core.types import Clue

from cno_bots.bots.operative import CNOOperativeBot
from cno_bots.bots.spymaster import CNOSpymasterBot


@dataclass(frozen=True, slots=True)
class PlayerBuildOptions:
    """Inputs for :func:`build_player` (CLI and tests use this)."""

    team: TeamColor
    role: Role
    room: str
    nickname: str
    random_operative: bool = False
    select_clue: Callable[[list[Clue]], Clue | None] | None = None
    rank_limit: int = 10


def build_player(options: PlayerBuildOptions) -> SpymasterPlayer | OperativePlayer:
    """Return a spymaster or operative bot wired to default clue/guess algorithms."""
    if options.role == "spymasters":
        return _build_spymaster(options)
    if options.role == "operatives":
        return _build_operative(options)
    raise ValueError(f"Unsupported role {options.role!r}")


def _build_spymaster(options: PlayerBuildOptions) -> SpymasterPlayer:
    clue_algorithm: ClueAlgorithm = CluegenClueAlgorithm()
    return CNOSpymasterBot(
        options.team,
        clue_algorithm,
        room=options.room,
        nickname=options.nickname,
        select_clue=options.select_clue,
        rank_limit=options.rank_limit,
    )


def _build_operative(options: PlayerBuildOptions) -> OperativePlayer:
    guess_algorithm: GuessAlgorithm = (
        RandomGuessAlgorithm()
        if options.random_operative
        else EmbeddingGuessAlgorithm()
    )
    return CNOOperativeBot(
        options.team,
        guess_algorithm,
        room=options.room,
        nickname=options.nickname,
    )
