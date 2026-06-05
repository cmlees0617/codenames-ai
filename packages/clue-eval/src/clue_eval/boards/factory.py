"""Generate synthetic Codenames boards for evaluation."""

from __future__ import annotations

import random
from pathlib import Path

from tqdm import tqdm

from clue_eval.boards.difficulty import DEFAULT_BETA, BoardDifficulty, board_difficulty
from clue_eval.boards.io import save_boards_to_json
from clue_eval.boards.types import BoardLayout, FixtureBoard
from clue_eval.embeddings.store import EmbeddingStore


def _combined_difficulty(score: BoardDifficulty) -> float:
    return (score.blue + score.red) / 2.0


def _layout_word_key(board: BoardLayout) -> tuple[str, ...]:
    all_words = board["blues"] + board["reds"] + board["civilians"] + board["assassins"]
    return tuple(sorted(all_words))


def _select_uniform_spread(
    scored: list[tuple[BoardLayout, BoardDifficulty]],
    n: int,
) -> list[tuple[BoardLayout, BoardDifficulty]]:
    """Pick ``n`` boards at evenly spaced quantiles of combined difficulty."""
    if n <= 0:
        return []
    if len(scored) < n:
        raise ValueError(f"Need at least {n} candidate boards, got {len(scored)}.")

    ranked = sorted(scored, key=lambda item: _combined_difficulty(item[1]))
    if n == 1:
        return [ranked[len(ranked) // 2]]

    last = len(ranked) - 1
    unique_indices: list[int] = []
    seen: set[int] = set()
    for index in range(n):
        position = int(round(index * last / (n - 1)))
        if position not in seen:
            unique_indices.append(position)
            seen.add(position)
    while len(unique_indices) < n:
        for position in range(len(ranked)):
            if position not in seen:
                unique_indices.append(position)
                seen.add(position)
                if len(unique_indices) == n:
                    break

    return [ranked[i] for i in unique_indices[:n]]


def _to_fixture_board(
    layout: BoardLayout,
    difficulty: BoardDifficulty,
    *,
    board_id: int,
) -> FixtureBoard:
    return {
        **layout,
        "id": board_id,
        "difficulty": difficulty.as_dict(),
    }


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
    def create_random_game(
        word_pool: list[str],
        *,
        rng: random.Random | None = None,
    ) -> BoardLayout:
        """
        Distribute 25 words into standard Codenames roles.

        9 blues (starting team), 8 reds, 7 civilians, 1 assassin.
        """
        if len(word_pool) < 25:
            raise ValueError("Word pool must have at least 25 words.")

        shuffled = list(word_pool)
        (rng or random).shuffle(shuffled)

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
        """Build a board around a known target cluster."""
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

    @staticmethod
    def generate_uniform_difficulty_boards(
        n: int,
        embeddings: EmbeddingStore,
        word_pool: list[str] | None = None,
        *,
        beta: float = DEFAULT_BETA,
        candidate_multiplier: int = 100,
        seed: int | None = None,
        show_progress: bool = False,
    ) -> list[FixtureBoard]:
        """
        Generate ``n`` boards with uniformly spaced mean difficulty.

        Difficulty per team in ``[0, 1]`` (``beta`` defaults to 2.0; higher = harder)::

            confusion / (confusion + cohesion)

        using ``log(1 + cos) / log(2)`` on non-negative pairs (negatives omitted).
        Boards with no scorable target–target pairs for a team are skipped. Confusion =
        + beta * log-max assassin; cohesion = log-mean pairwise among targets.

        Process:
        1. Sample ``n * candidate_multiplier`` unique random 25-card layouts.
        2. Score blue and red difficulty via :func:`~clue_eval.boards.difficulty.board_difficulty`.
        3. Select ``n`` boards at even quantiles of (blue + red) / 2.

        Returns :class:`~clue_eval.boards.types.FixtureBoard` dicts with
        ``id`` and ``difficulty: {blue, red}``.
        """
        if n < 1:
            raise ValueError("n must be at least 1")

        pool = list(word_pool if word_pool is not None else embeddings.words)
        if len(pool) < 25:
            raise ValueError("Word pool must have at least 25 words.")

        rng = random.Random(seed)
        candidate_count = max(n * candidate_multiplier, n)
        scored: list[tuple[BoardLayout, BoardDifficulty]] = []
        seen: set[tuple[str, ...]] = set()

        attempts = 0
        max_attempts = candidate_count * 20
        with tqdm(
            total=candidate_count,
            desc="Scoring candidate boards",
            unit="board",
            disable=not show_progress,
        ) as progress:
            while len(scored) < candidate_count and attempts < max_attempts:
                attempts += 1
                layout = BoardFactory.create_random_game(pool, rng=rng)
                key = _layout_word_key(layout)
                if key in seen:
                    continue
                difficulty = board_difficulty(layout, embeddings, beta=beta)
                if difficulty is None:
                    continue
                seen.add(key)
                scored.append((layout, difficulty))
                progress.update(1)

        if len(scored) < n:
            raise ValueError(
                f"Only found {len(scored)} unique boards (need {n}). "
                "Increase candidate_multiplier or word pool size."
            )

        selected = _select_uniform_spread(scored, n)
        return [
            _to_fixture_board(layout, difficulty, board_id=index + 1)
            for index, (layout, difficulty) in enumerate(selected)
        ]

    @staticmethod
    def generate_and_save_uniform_difficulty_boards(
        n: int,
        embeddings: EmbeddingStore,
        output_path: Path,
        word_pool: list[str] | None = None,
        *,
        beta: float = DEFAULT_BETA,
        candidate_multiplier: int = 100,
        seed: int | None = None,
        sort_by_difficulty: bool = True,
        show_progress: bool = False,
    ) -> Path:
        """
        Generate boards, then save to ``output_path`` ordered easiest → hardest.

        See :meth:`generate_uniform_difficulty_boards` for generation parameters.
        """
        boards = BoardFactory.generate_uniform_difficulty_boards(
            n,
            embeddings,
            word_pool,
            beta=beta,
            candidate_multiplier=candidate_multiplier,
            seed=seed,
            show_progress=show_progress,
        )
        return save_boards_to_json(output_path, boards, sort_by_difficulty=sort_by_difficulty)
