import json
from pathlib import Path
from src.algos import CodenamesSpymaster

def load_boards_from_json(filename: str) -> list[dict]:
    """
    Load test boards from JSON file.

    Parameters:
        filename: name of JSON file.
    """
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError as e:
        print("File not found")


def main():
    ROOT_DIR = Path(__file__).parent
    DATA_DIR = ROOT_DIR / "data"
    
    # Initialize a spymaster
    spymaster = CodenamesSpymaster()
    
    # Select the vocabulary using the resolved path
    vocab_path = DATA_DIR / "advanced_vocab.txt"
    spymaster.load_vocabulary(str(vocab_path), verbose=True)

    # Initialize the game board
    board_path = DATA_DIR / "test_boards.json"
    boards = load_boards_from_json(board_path)
    
    # Select a game board
    board = boards[0]

    targets = board["reds"]
    civilians = board["civilians"]
    enemies = board["blues"]
    assassins = board["assassins"]
    
    # Load game board into Spymaster
    spymaster.initialize_game_board(targets + civilians + enemies + assassins)
    spymaster.update_board_state(
        targets=targets,
        civilians=civilians,
        enemies=enemies,
        assassins=assassins
    )
    spymaster.prune_vocabulary()

    # Generate Clue
    clue = spymaster.generate_clue(min_targets=1, max_targets=3, verbose=True)
    print(clue)

if __name__ == "__main__":
    main()