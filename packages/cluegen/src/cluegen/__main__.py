"""Run the offline clue generation demo."""

from __future__ import annotations

from pathlib import Path

from cluegen.clue_engine import ClueEngine
from cluegen.guess_engine import EmbeddingGuessEngine, LLMGuessEngine
from cluegen.utils import load_boards_from_json


def main() -> None:
    data_dir = Path(__file__).resolve().parents[2] / "data"
    engine = ClueEngine()
    engine.load_vocabulary(str(data_dir / "simple_vocab.txt"), verbose=True)

    boards = load_boards_from_json(data_dir / "test_boards.json")
    board = boards[0]

    targets = board["blues"]
    civilians = board["civilians"]
    enemies = board["reds"]
    assassins = board["assassins"]

    engine.initialize_game_board(targets + civilians + enemies + assassins)
    engine.update_board_state(
        targets=targets,
        civilians=civilians,
        enemies=enemies,
        assassins=assassins,
    )
    engine.prune_vocabulary()
    clue = engine.generate_clue(min_targets=1, max_targets=3, verbose=True)
    print(clue)

    embedding_guesser = EmbeddingGuessEngine()
    embedding_guesser.update_board_state(targets + civilians + enemies + assassins)
    embedding_guesses = embedding_guesser.guess(
        clue=clue["word"],
        count=len(clue["intended_targets"]),
    )
    print(f"Embedding guesses: {embedding_guesses}")

    llm_guesser = LLMGuessEngine()
    llm_guesser.update_board_state(targets + civilians + enemies + assassins)
    llm_guesses = llm_guesser.guess(
        clue=clue["word"],
        count=len(clue["intended_targets"]),
    )
    print(f"LLM guesses: {llm_guesses}")


if __name__ == "__main__":
    main()
