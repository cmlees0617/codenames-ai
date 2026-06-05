"""Cluegen-backed clue ranking."""

from __future__ import annotations

import contextlib
import io
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from game_core.types import Clue
from game_core.views import SpymasterView

if TYPE_CHECKING:
    from cluegen.clue_engine import ClueEngine

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
    """
    Rank clues using semantic embeddings (cluegen ``ClueEngine``).

    Implements :class:`~game_core.algorithms.ClueAlgorithm` and exposes
    :attr:`name` for :class:`~game_core.algorithms.IdentifiableClueAlgorithm`
    benchmark output files.
    """

    name = "cluegen"

    def __init__(
        self,
        *,
        vocab_path: Path | None = None,
        prune_vocabulary: bool = True,
    ) -> None:
        self._vocab_path = vocab_path or default_vocab_path()
        self._prune_vocabulary = prune_vocabulary
        self._engine: ClueEngine | None = None
        self._board_words: tuple[str, ...] | None = None

    def engine_for_debug(self) -> ClueEngine:
        """Return the loaded engine after :meth:`rank_clues` (local debugging / viz only)."""
        if self._engine is None:
            raise RuntimeError("Call rank_clues before accessing the engine.")
        return self._engine

    def _ensure_loaded(self) -> ClueEngine:
        from cluegen.clue_engine import ClueEngine

        if self._engine is None:
            logger.info("Loading clue vocabulary from %s...", self._vocab_path)
            engine = ClueEngine()
            with contextlib.redirect_stdout(io.StringIO()):
                engine.load_vocabulary(str(self._vocab_path))
            self._engine = engine
            logger.info("Clue vocabulary ready.")
        return self._engine

    def _ensure_board(self, state: SpymasterView) -> None:
        board_words = tuple(card.word for card in state.board)
        if self._board_words == board_words:
            return
        engine = self._ensure_loaded()
        with contextlib.redirect_stdout(io.StringIO()):
            engine.initialize_game_board(list(board_words))
        self._board_words = board_words

    def rank_clues(self, state: SpymasterView, *, limit: int = 10) -> list[Clue]:
        targets, civilians, enemies, assassins = _categories_from_view(state)
        if not targets:
            return []

        self._ensure_board(state)
        engine = self._ensure_loaded()
        max_targets = min(MAX_TARGETS, len(targets))

        with contextlib.redirect_stdout(io.StringIO()):
            engine.update_board_state(
                targets=targets,
                civilians=civilians,
                enemies=enemies,
                assassins=assassins,
            )
            if self._prune_vocabulary:
                engine.reset_vocabulary()
                engine.prune_vocabulary()
            results = engine.generate_ranked_clues(
                min_targets=1,
                max_targets=max_targets,
                limit=limit,
            )

        clues = [_result_to_clue(result) for result in results if result.get("word")]
        return clues[:limit]
