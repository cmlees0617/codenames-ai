"""Run the offline clue generation demo."""

from __future__ import annotations

import json
from pathlib import Path

from cluegen.algos import CodenamesSpymaster


def load_boards_from_json(filename: Path) -> list[dict]:
    with open(filename, encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    data_dir = Path(__file__).resolve().parents[2] / "data"
    spymaster = CodenamesSpymaster()
    spymaster.load_vocabulary(str(data_dir / "advanced_vocab.txt"), verbose=True)

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


if __name__ == "__main__":
    main()
