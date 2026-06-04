"""Cluegen-backed clue ranking."""

from __future__ import annotations

import contextlib
from typing import Any
import io
import logging
from pathlib import Path

from game_core.types import Clue
from game_core.views import SpymasterView

from cluegen.spymaster import Spymaster

logger = logging.getLogger(__name__)

DEFAULT_VOCAB = "standard_vocab.txt"
MAX_TARGETS = 3


def default_vocab_path() -> Path:
    return Path(__file__).resolve().parents[3] / "data" / DEFAULT_VOCAB


def _enemy_team(team: str) -> str:
    return "blue" if team == "red" else "red"


def _categories_from_view(
    state: SpymasterView,
) -> tuple[list[str], list[str], list[str], list[str]]:
    opponent = _enemy_team(state.team)
    targets: list[str] = []
    civilians: list[str] = []
    enemies: list[str] = []
    assassins: list[str] = []

    for card in state.board:
        if card.revealed:
            continue
        if card.color == state.team:
            targets.append(card.word)
        elif card.color == opponent:
            enemies.append(card.word)
        elif card.color == "civilian":
            civilians.append(card.word)
        elif card.color == "assassin":
            assassins.append(card.word)

    return targets, civilians, enemies, assassins


def _result_to_clue(result: dict[str, Any]) -> Clue:
    targets = tuple(result["intended_targets"])
    return Clue(
        word=result["word"],
        count=len(targets),
        intended_targets=targets,
    )


class CluegenClueAlgorithm:
    """Rank clues using semantic embeddings (cluegen Spymaster engine)."""

    def __init__(self, *, vocab_path: Path | None = None) -> None:
        self._vocab_path = vocab_path or default_vocab_path()
        self._spymaster: Spymaster | None = None
        self._board_words: tuple[str, ...] | None = None

    def _ensure_loaded(self) -> Spymaster:
        if self._spymaster is None:
            logger.info("Loading clue vocabulary from %s...", self._vocab_path)
            spymaster = Spymaster()
            with contextlib.redirect_stdout(io.StringIO()):
                spymaster.load_vocabulary(str(self._vocab_path))
            self._spymaster = spymaster
            logger.info("Clue vocabulary ready.")
        return self._spymaster

    def _ensure_board(self, state: SpymasterView) -> None:
        board_words = tuple(card.word for card in state.board)
        if self._board_words == board_words:
            return
        spymaster = self._ensure_loaded()
        with contextlib.redirect_stdout(io.StringIO()):
            spymaster.initialize_game_board(list(board_words))
        self._board_words = board_words

    def rank_clues(self, state: SpymasterView, *, limit: int = 10) -> list[Clue]:
        targets, civilians, enemies, assassins = _categories_from_view(state)
        if not targets:
            return []

        self._ensure_board(state)
        spymaster = self._ensure_loaded()
        max_targets = min(MAX_TARGETS, len(targets))

        with contextlib.redirect_stdout(io.StringIO()):
            spymaster.update_board_state(
                targets=targets,
                civilians=civilians,
                enemies=enemies,
                assassins=assassins,
            )
            spymaster.prune_vocabulary()
            results = spymaster.generate_ranked_clues(
                min_targets=1,
                max_targets=max_targets,
                limit=limit,
            )

        clues = [_result_to_clue(result) for result in results if result.get("word")]
        return clues[:limit]
