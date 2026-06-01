"""Run the offline clue generation demo."""

from __future__ import annotations

from pathlib import Path

from cluegen.spymaster import Spymaster
from cluegen.operative import EmbeddingOperative, LLMOperative
from cluegen.utils import load_boards_from_json


def main() -> None:
    data_dir = Path(__file__).resolve().parents[2] / "data"
    spymaster = Spymaster()
    spymaster.load_vocabulary(str(data_dir / "simple_vocab.txt"), verbose=True)

    boards = load_boards_from_json(data_dir / "test_boards.json")
    board = boards[0]

    targets = board["blues"]
    civilians = board["civilians"]
    enemies = board["reds"]
    assassins = board["assassins"]

    spymaster.initialize_game_board(targets + civilians + enemies + assassins)
    spymaster.update_board_state(
        targets=targets,
        civilians=civilians,
        enemies=enemies,
        assassins=assassins,
    )
    spymaster.prune_vocabulary()
    clue = spymaster.generate_clue(min_targets=1, max_targets=3, verbose=True)
    print(clue)


    # Try to guess words based on the clue
    embedding_operative = EmbeddingOperative()
    embedding_operative.update_board_state(targets + civilians + enemies + assassins)
    embedding_guesses = embedding_operative.guess(clue=clue["word"], count=len(clue["intended_targets"]))
    print(f"Embedding Operative Guesses: {embedding_guesses}")

    llm_operative = LLMOperative()
    llm_operative.update_board_state(targets + civilians + enemies + assassins)
    llm_guesses = llm_operative.guess(clue=clue["word"], count=len(clue["intended_targets"]))
    print(f"LLM Operative Guesses: {llm_guesses}")


if __name__ == "__main__":
    main()
