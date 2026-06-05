"""Codenames spymaster clue legality (offline rule checks)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Literal

from metaphone import doublemetaphone
from nltk.stem import SnowballStemmer, WordNetLemmatizer

from clue_eval.boards.types import BoardLayout
from clue_eval.operatives.views import iter_board_words

RuleId = Literal["single_token", "stem_or_lemma", "homophone", "min_count"]

_TOKEN_PATTERN = re.compile(r"^[^\s]+$", re.UNICODE)


@dataclass(frozen=True, slots=True)
class ClueLegalityViolation:
    """One failed legality rule."""

    rule: RuleId
    message: str


@dataclass(frozen=True, slots=True)
class ClueLegalityResult:
    """Outcome of all spymaster clue legality checks."""

    legal: bool
    violations: tuple[ClueLegalityViolation, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "legal": self.legal,
            "violations": [
                {"rule": violation.rule, "message": violation.message}
                for violation in self.violations
            ],
        }


def visible_words_from_board(board: BoardLayout) -> list[str]:
    """All words currently on the board (uppercase), for legality checks."""
    return [word.upper() for word in iter_board_words(board)]


def validate_clue_legality(
    clue_word: str,
    count: int,
    visible_board_words: list[str],
) -> ClueLegalityResult:
    """
    Check whether a spymaster clue obeys standard Codenames word/number rules.

    Rules:
    1. Clue word is exactly one non-empty token (no spaces).
    2. Clue does not share a stem or lemma with any visible board word.
    3. Clue is not a homophone of any visible board word (Double Metaphone).
    4. Count is at least 1.
    """
    violations: list[ClueLegalityViolation] = []
    normalized_visible = [word.upper() for word in visible_board_words if word.strip()]

    violations.extend(_check_single_token(clue_word))
    if count < 1:
        violations.append(
            ClueLegalityViolation(
                rule="min_count",
                message=f"Count must be at least 1, got {count}.",
            )
        )

    token = _normalize_clue_token(clue_word)
    if token is not None:
        violations.extend(_check_stem_and_lemma(token, normalized_visible))
        violations.extend(_check_homophones(token, normalized_visible))

    return ClueLegalityResult(legal=not violations, violations=tuple(violations))


def is_legal_clue(
    clue_word: str,
    count: int,
    visible_board_words: list[str],
) -> bool:
    """Return ``True`` when ``validate_clue_legality`` reports no violations."""
    return validate_clue_legality(clue_word, count, visible_board_words).legal


def _normalize_clue_token(clue_word: str) -> str | None:
    stripped = clue_word.strip()
    if not stripped:
        return None
    parts = stripped.split()
    if len(parts) != 1:
        return None
    return parts[0].upper()


def _check_single_token(clue_word: str) -> list[ClueLegalityViolation]:
    stripped = clue_word.strip()
    if not stripped:
        return [
            ClueLegalityViolation(
                rule="single_token",
                message="Clue word must not be empty.",
            )
        ]

    parts = stripped.split()
    if len(parts) != 1:
        return [
            ClueLegalityViolation(
                rule="single_token",
                message=f"Clue must be exactly one token, got {len(parts)}: {stripped!r}.",
            )
        ]

    token = parts[0]
    if not _TOKEN_PATTERN.fullmatch(token):
        return [
            ClueLegalityViolation(
                rule="single_token",
                message=f"Clue must be a single whitespace-delimited token, got {token!r}.",
            )
        ]
    return []


def _check_stem_and_lemma(
    clue_token: str,
    visible_board_words: list[str],
) -> list[ClueLegalityViolation]:
    stemmer, lemmatizer = _english_stemmer_and_lemmatizer()
    clue_lower = clue_token.lower()
    clue_stem = stemmer.stem(clue_lower)
    clue_lemma = lemmatizer.lemmatize(clue_lower)

    for word in visible_board_words:
        word_lower = word.lower()
        word_stem = stemmer.stem(word_lower)
        word_lemma = lemmatizer.lemmatize(word_lower)

        if clue_lower == word_lower:
            return [
                ClueLegalityViolation(
                    rule="stem_or_lemma",
                    message=f"Clue {clue_token!r} matches board word {word!r}.",
                )
            ]

        if clue_lower in word_lower or word_lower in clue_lower:
            return [
                ClueLegalityViolation(
                    rule="stem_or_lemma",
                    message=(
                        f"Clue {clue_token!r} is a substring of (or contains) board word {word!r}."
                    ),
                )
            ]

        if _morphology_overlap(clue_stem, word_stem) or _morphology_overlap(clue_lemma, word_lemma):
            return [
                ClueLegalityViolation(
                    rule="stem_or_lemma",
                    message=(
                        f"Clue {clue_token!r} shares a stem or lemma with board word {word!r}."
                    ),
                )
            ]

    return []


def _morphology_overlap(left: str, right: str) -> bool:
    return left in right or right in left


def _check_homophones(
    clue_token: str,
    visible_board_words: list[str],
) -> list[ClueLegalityViolation]:
    clue_codes = _double_metaphone_codes(clue_token)
    if not clue_codes:
        return []

    for word in visible_board_words:
        if word == clue_token:
            continue
        word_codes = _double_metaphone_codes(word)
        if clue_codes & word_codes:
            return [
                ClueLegalityViolation(
                    rule="homophone",
                    message=f"Clue {clue_token!r} is a homophone of board word {word!r}.",
                )
            ]
    return []


def _double_metaphone_codes(word: str) -> frozenset[str]:
    primary, secondary = doublemetaphone(word.lower())
    return frozenset(code for code in (primary, secondary) if code)


@lru_cache(maxsize=1)
def _english_stemmer_and_lemmatizer() -> tuple[SnowballStemmer, WordNetLemmatizer]:
    _ensure_wordnet()
    return SnowballStemmer("english"), WordNetLemmatizer()


def _ensure_wordnet() -> None:
    import nltk

    for package in ("wordnet", "omw-1.4"):
        nltk.download(package, quiet=True)
