"""Generate synthetic Codenames boards for evaluation."""

from __future__ import annotations

import random
from pathlib import Path

from clue_eval.boards.types import BoardLayout


class BoardFactory:
    """Tools for generating synthetic Codenames boards."""

    @staticmethod
    def from_vocab_file(filepath: Path, count: int = 25) -> list[str]:
        """Load a word pool from a vocab file and sample ``count`` candidates."""
        with filepath.open(encoding="utf-8") as handle:
            words = [line.strip().upper() for line in handle if line.strip()]
        if len(words) < count:
            raise ValueError(f"Vocab file only has {len(words)} words; requested {count}.")
        return random.sample(words, count)

    @staticmethod
    def create_random_game(word_pool: list[str]) -> BoardLayout:
        """
        Distribute 25 words into standard Codenames roles.

        Distribution: 9 starting-team cards, 8 opposing, 7 civilians, 1 assassin.
        ``blues`` are treated as the starting team in fixtures (matches ``test_boards.json``).
        """
        if len(word_pool) < 25:
            raise ValueError("Word pool must have at least 25 words.")

        shuffled = list(word_pool)
        random.shuffle(shuffled)

        return {
            "blues": shuffled[0:9],
            "reds": shuffled[9:17],
            "civilians": shuffled[17:24],
            "assassins": [shuffled[24]],
        }

    @staticmethod
    def create_clue_set(
        targets: list[str],
        pool: list[str],
        *,
        civilian_count: int = 5,
        enemy_count: int = 5,
    ) -> BoardLayout:
        """Build a board around a known target cluster (debugging / catalog cases)."""
        remaining = [word for word in pool if word not in targets]
        needed = civilian_count + enemy_count + 1
        if len(remaining) < needed:
            raise ValueError("Word pool too small for requested board constraints.")

        random.shuffle(remaining)
        civs = remaining[:civilian_count]
        enemies = remaining[civilian_count : civilian_count + enemy_count]
        assassin_start = civilian_count + enemy_count

        return {
            "blues": list(targets),
            "civilians": civs,
            "reds": enemies,
            "assassins": remaining[assassin_start : assassin_start + 1],
        }