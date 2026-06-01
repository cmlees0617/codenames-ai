# packages/cluegen/src/cluegen/utils.py

import json
from pathlib import Path

def load_boards_from_json(filename: Path) -> list[dict]:
    """
    Loads all boards from the given JSON file and returns them as a list of dictionaries.
    """
    try:
        with open(filename, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"File not found: {filename}")
        return []
    except json.JSONDecodeError:
        print(f"Invalid JSON in file: {filename}")
        return []