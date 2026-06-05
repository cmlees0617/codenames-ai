"""Score operative guesses against a hidden board layout."""

from __future__ import annotations

from game_core.types import TeamColor

from clue_eval.boards.types import BoardLayout


def team_words(board: BoardLayout, team: TeamColor) -> frozenset[str]:
    key = "blues" if team == "blue" else "reds"
    return frozenset(word.upper() for word in board[key])


def opponent_words(board: BoardLayout, team: TeamColor) -> frozenset[str]:
    key = "reds" if team == "blue" else "blues"
    return frozenset(word.upper() for word in board[key])


def score_operative_guesses(
    board: BoardLayout,
    team: TeamColor,
    guesses: list[str],
) -> dict[str, object]:
    """Summarize how operative guesses align with hidden colors."""
    normalized = [word.upper() for word in guesses]
    ours = team_words(board, team)
    theirs = opponent_words(board, team)
    civilians = frozenset(word.upper() for word in board["civilians"])
    assassins = frozenset(word.upper() for word in board["assassins"])

    team_hits = [word for word in normalized if word in ours]
    opponent_hits = [word for word in normalized if word in theirs]
    civilian_hits = [word for word in normalized if word in civilians]
    assassin_hits = [word for word in normalized if word in assassins]

    return {
        "guesses": normalized,
        "team_hits": team_hits,
        "team_hit_count": len(team_hits),
        "opponent_hits": opponent_hits,
        "civilian_hits": civilian_hits,
        "assassin_hits": assassin_hits,
        "hit_assassin": bool(assassin_hits),
    }
