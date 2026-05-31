"""Bridge codenames.game state to cluegen clue generation."""

from __future__ import annotations

import contextlib
import io
import logging
from dataclasses import dataclass
from pathlib import Path

from cno_sdk.state import GameState, TeamColor
from cluegen.algos import CodenamesSpymaster

logger = logging.getLogger(__name__)

DEFAULT_VOCAB = "standard_vocab.txt"
MAX_TARGETS = 3


def default_vocab_path() -> Path:
    return Path(__file__).resolve().parents[3] / "cluegen" / "data" / DEFAULT_VOCAB


def enemy_team(team: TeamColor) -> TeamColor:
    return "blue" if team == "red" else "red"


@dataclass(frozen=True)
class BoardCategories:
    targets: list[str]
    civilians: list[str]
    enemies: list[str]
    assassins: list[str]


def board_categories(state: GameState, team: TeamColor) -> BoardCategories:
    """Split unrevealed cards into cluegen board buckets for ``team``."""
    opponent = enemy_team(team)
    targets: list[str] = []
    civilians: list[str] = []
    enemies: list[str] = []
    assassins: list[str] = []

    for card in state.grid:
        if card.revealed:
            continue
        if card.color == team:
            targets.append(card.word)
        elif card.color == opponent:
            enemies.append(card.word)
        elif card.color == "neutral":
            civilians.append(card.word)
        elif card.color == "black":
            assassins.append(card.word)

    return BoardCategories(
        targets=targets,
        civilians=civilians,
        enemies=enemies,
        assassins=assassins,
    )


@dataclass(frozen=True)
class GeneratedClue:
    word: str
    targets: list[str]


class ClueEngine:
    """Lazy-loaded cluegen wrapper for live spymaster turns."""

    def __init__(self, *, vocab_path: Path | None = None) -> None:
        self._vocab_path = vocab_path or default_vocab_path()
        self._spymaster: CodenamesSpymaster | None = None
        self._board_words: tuple[str, ...] | None = None

    def _ensure_loaded(self) -> CodenamesSpymaster:
        if self._spymaster is None:
            logger.info("Loading clue vocabulary from %s...", self._vocab_path)
            spymaster = CodenamesSpymaster()
            with contextlib.redirect_stdout(io.StringIO()):
                spymaster.load_vocabulary(str(self._vocab_path))
            self._spymaster = spymaster
            logger.info("Clue vocabulary ready.")
        return self._spymaster

    def _ensure_board(self, state: GameState) -> None:
        board_words = tuple(card.word for card in state.grid)
        if self._board_words == board_words:
            return
        spymaster = self._ensure_loaded()
        with contextlib.redirect_stdout(io.StringIO()):
            spymaster.initialize_game_board(list(board_words))
        self._board_words = board_words

    def generate(self, state: GameState, team: TeamColor) -> GeneratedClue:
        categories = board_categories(state, team)
        if not categories.targets:
            raise ValueError("No unrevealed friendly cards to clue")

        self._ensure_board(state)
        spymaster = self._ensure_loaded()
        max_targets = min(MAX_TARGETS, len(categories.targets))

        with contextlib.redirect_stdout(io.StringIO()):
            spymaster.update_board_state(
                targets=categories.targets,
                civilians=categories.civilians,
                enemies=categories.enemies,
                assassins=categories.assassins,
            )
            spymaster.prune_vocabulary()
            result = spymaster.generate_clue(
                min_targets=1,
                max_targets=max_targets,
            )

        targets = list(result["intended_targets"])
        if not result["word"] or not targets:
            raise ValueError("Cluegen returned an empty clue")

        return GeneratedClue(word=result["word"], targets=targets)
