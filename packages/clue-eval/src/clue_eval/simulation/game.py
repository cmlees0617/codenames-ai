"""Simulate one full Codenames game on a fixed board."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Literal

from game_core.algorithms import ClueAlgorithm, GuessAlgorithm
from game_core.types import Clue, TeamColor

from clue_eval.boards.types import FixtureBoard
from clue_eval.clues.legality import validate_clue_legality, visible_words_from_board
from clue_eval.simulation.difficulty import difficulty_fields_for_board
from clue_eval.simulation.state import (
    BoardGameState,
    opponent_team,
    spymaster_team_for_board,
    tile_color_for_team,
)

GameOutcome = Literal["win", "loss", "abort"]
LossReason = Literal["assassin", "opponent"]


@dataclass(frozen=True, slots=True)
class SimulatedGameResult:
    """
    Result of one simulated game on a single board.

    ``abort_reason`` is set only when ``outcome`` is ``abort`` (illegal spymaster clue).
    """

    board_id: int | None
    outcome: GameOutcome
    test_team: TeamColor
    turns: int
    opponent_turns: int
    abort_reason: str | None = None  # set only when the spymaster clue fails legality checks
    loss_reason: LossReason | None = None
    last_clue: str | None = None
    difficulty_blue: float | None = None
    difficulty_red: float | None = None
    difficulty_mean: float | None = None
    difficulty_test_team: float | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "board_id": self.board_id,
            "outcome": self.outcome,
            "test_team": self.test_team,
            "turns": self.turns,
            "opponent_turns": self.opponent_turns,
            "abort_reason": self.abort_reason,
            "loss_reason": self.loss_reason,
            "last_clue": self.last_clue,
            "difficulty_blue": self.difficulty_blue,
            "difficulty_red": self.difficulty_red,
            "difficulty_mean": self.difficulty_mean,
            "difficulty_test_team": self.difficulty_test_team,
        }


def _make_result(
    board: FixtureBoard,
    team: TeamColor,
    *,
    outcome: GameOutcome,
    turns: int,
    opponent_turns: int,
    abort_reason: str | None = None,
    loss_reason: LossReason | None = None,
    last_clue: str | None = None,
) -> SimulatedGameResult:
    difficulty = difficulty_fields_for_board(board, team)
    return SimulatedGameResult(
        board_id=board.get("id"),
        outcome=outcome,
        test_team=team,
        turns=turns,
        opponent_turns=opponent_turns,
        abort_reason=abort_reason,
        loss_reason=loss_reason,
        last_clue=last_clue,
        **difficulty,
    )


def simulate_game(
    board: FixtureBoard,
    spymaster: ClueAlgorithm,
    operative: GuessAlgorithm,
    *,
    rng: random.Random | None = None,
    clue_limit: int = 10,
) -> SimulatedGameResult:
    """
    Play out a game with the test spymaster + operative on the larger team.

    Each test-team turn: one clue (must be legal) then at most ``clue.count`` operative
    word guesses (never ``count + 1``). The turn ends early on a wrong guess; the
    operative cannot pass voluntarily. After the turn, the opponent reveals one
    unrevealed word on their team (perfect guess). **Loss** on assassin hit or when
    all opponent words are revealed. **Abort** only when the spymaster clue fails
    :func:`~clue_eval.clues.legality.validate_clue_legality` (including no clue / empty word).
    """
    random_source = rng or random.Random()
    state = BoardGameState.from_layout(board)
    team = spymaster_team_for_board(board)
    turns = 0
    opponent_turns = 0
    last_clue: str | None = None

    while True:
        if state.team_words_remaining(team) == 0:
            return _make_result(
                board,
                team,
                outcome="win",
                turns=turns,
                opponent_turns=opponent_turns,
                last_clue=last_clue,
            )

        if state.team_words_remaining(opponent_team(team)) == 0:
            return _make_result(
                board,
                team,
                outcome="loss",
                turns=turns,
                opponent_turns=opponent_turns,
                loss_reason="opponent",
                last_clue=last_clue,
            )

        view = state.spymaster_view(team)
        clues = spymaster.rank_clues(view, limit=clue_limit)
        visible = visible_words_from_board(board)
        if not clues:
            legality = validate_clue_legality("", 1, visible)
            reason = (
                "; ".join(violation.message for violation in legality.violations)
                or "Illegal clue"
            )
            return _make_result(
                board,
                team,
                outcome="abort",
                turns=turns,
                opponent_turns=opponent_turns,
                abort_reason=reason,
                last_clue=last_clue,
            )

        clue, abort_reason = _select_playable_clue(clues, visible, operative)
        if clue is None:
            return _make_result(
                board,
                team,
                outcome="abort",
                turns=turns,
                opponent_turns=opponent_turns,
                abort_reason=abort_reason or "No playable clue",
                last_clue=last_clue,
            )

        last_clue = clue.word

        phase_result = _run_operative_phase(state, team, clue, operative)
        turns += 1

        if phase_result == "loss":
            return _make_result(
                board,
                team,
                outcome="loss",
                turns=turns,
                opponent_turns=opponent_turns,
                loss_reason="assassin",
                last_clue=last_clue,
            )
        if phase_result == "win":
            return _make_result(
                board,
                team,
                outcome="win",
                turns=turns,
                opponent_turns=opponent_turns,
                last_clue=last_clue,
            )

        revealed = state.reveal_random_opponent_word(team, random_source)
        if revealed is not None:
            opponent_turns += 1

        if state.team_words_remaining(opponent_team(team)) == 0:
            return _make_result(
                board,
                team,
                outcome="loss",
                turns=turns,
                opponent_turns=opponent_turns,
                loss_reason="opponent",
                last_clue=last_clue,
            )


def _select_playable_clue(
    clues: list[Clue],
    visible: list[str],
    operative: GuessAlgorithm,
) -> tuple[Clue | None, str | None]:
    """
    Return the first ranked clue that is legal and supported by the operative.

    Embedding operatives skip clue words with no vector in the full GloVe model.
    """
    supports = getattr(operative, "supports_clue_word", None)
    last_legality_reason: str | None = None

    for candidate in clues:
        legality = validate_clue_legality(candidate.word, candidate.count, visible)
        if not legality.legal:
            last_legality_reason = (
                "; ".join(violation.message for violation in legality.violations)
                or "Illegal clue"
            )
            continue
        if callable(supports) and not supports(candidate.word):
            continue
        return candidate, None

    if last_legality_reason is not None:
        return None, last_legality_reason
    return None, "No clue word encodable in operative GloVe model"


def _run_operative_phase(
    state: BoardGameState,
    team: TeamColor,
    clue: Clue,
    operative: GuessAlgorithm,
) -> GameOutcome | None:
    """
    Up to ``clue.count`` word guesses (no ``count + 1`` bonus).

    Wrong card (civilian or opponent) or voluntary pass ends the turn without abort.
    """
    required = clue.count

    op_state = state.operative_view(
        team,
        clue_word=clue.word,
        clue_count=clue.count,
        guesses_remaining=required,
    )

    for _ in range(required):
        if op_state.guesses_remaining <= 0:
            break

        action = operative.guess_word(op_state)
        if action.pass_turn or action.word is None:
            return None

        word = action.word
        if state.is_revealed(word):
            op_state = _decrement_guesses(op_state)
            continue

        color = state.reveal(word)
        op_state = _mark_revealed_on_view(op_state, word)

        if color == "assassin":
            return ("loss", None)

        if color == tile_color_for_team(team):
            if state.team_words_remaining(team) == 0:
                return ("win", None)
            continue

        return (None, None)

    return (None, None)


def _decrement_guesses(state):
    from game_core.views import OperativeView

    return OperativeView(
        team=state.team,
        board=state.board,
        current_clue=state.current_clue,
        guesses_remaining=max(0, state.guesses_remaining - 1),
        clue_history=state.clue_history,
        gameover=state.gameover,
    )


def _mark_revealed_on_view(state, word: str):
    from game_core.views import BoardTileView, OperativeView

    upper = word.upper()
    updated = tuple(
        BoardTileView(
            word=tile.word,
            revealed=tile.revealed or tile.word == upper,
            color=tile.color,
        )
        for tile in state.board
    )
    return OperativeView(
        team=state.team,
        board=updated,
        current_clue=state.current_clue,
        guesses_remaining=max(0, state.guesses_remaining - 1),
        clue_history=state.clue_history,
        gameover=state.gameover,
    )
