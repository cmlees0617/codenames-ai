"""Run one operative turn against a ranked spymaster clue."""

from __future__ import annotations

from typing import Any

from game_core.algorithms import GuessAlgorithm
from game_core.types import Clue, TeamColor

from clue_eval.boards.types import BoardLayout
from clue_eval.operatives.scoring import score_operative_guesses
from clue_eval.operatives.views import apply_guess, board_layout_to_operative_view


def collect_operative_guesses(
    board: BoardLayout,
    team: TeamColor,
    clue: Clue,
    guess_algorithm: GuessAlgorithm,
) -> list[str]:
    """Ask the operative for up to ``clue.count`` guesses (one per protocol call)."""
    state = board_layout_to_operative_view(
        board,
        team=team,
        clue_word=clue.word,
        clue_count=clue.count,
        guesses_remaining=clue.count,
    )
    guesses: list[str] = []
    for _ in range(clue.count):
        if state.guesses_remaining <= 0:
            break
        action = guess_algorithm.guess_word(state)
        if action.pass_turn or action.word is None:
            break
        guesses.append(action.word)
        state = apply_guess(state, action.word)
    return guesses


def evaluate_operative_turn(
    board: BoardLayout,
    team: TeamColor,
    clue: Clue,
    guess_algorithm: GuessAlgorithm,
) -> dict[str, Any]:
    """Run the operative and return guess list plus hidden-color scoring."""
    guesses = collect_operative_guesses(board, team, clue, guess_algorithm)
    scoring = score_operative_guesses(board, team, guesses)
    return {
        "clue_word": clue.word,
        "clue_count": clue.count,
        **scoring,
    }
