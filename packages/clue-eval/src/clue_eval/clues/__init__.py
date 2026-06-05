"""Spymaster clue validation for offline evaluation."""

from clue_eval.clues.legality import (
    ClueLegalityResult,
    ClueLegalityViolation,
    is_legal_clue,
    validate_clue_legality,
    visible_words_from_board,
)

__all__ = [
    "ClueLegalityResult",
    "ClueLegalityViolation",
    "is_legal_clue",
    "validate_clue_legality",
    "visible_words_from_board",
]
