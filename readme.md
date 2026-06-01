# codenames-ai

Python tools for playing [Codenames Online](https://codenames.game): a protocol SDK, a CLI bot, and an offline clue engine.

## Packages

| Package | Description |
|---------|-------------|
| `cno-sdk` | Low-level Socket.IO / boardgame.io client for codenames.game |
| `cno` | CLI and high-level bot sessions (`cno` command) |
| `cluegen` | Offline clue generation using semantic embeddings |

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)

## Setup

```bash
git clone <repo-url>
cd codenames-ai
uv sync --all-packages --group dev
```

## Quickstart

Run the interactive CLI (no arguments) — pick a role, enter a room slug, and optionally customize your nickname:

```bash
uv run cno
```

Or pass arguments directly:

```bash
# Join an existing room as red spymaster
uv run cno halok-jonah red-spymaster

# Blue operative with a custom nickname
uv run cno halok-jonah blue-operative --nickname MyBot
```

Roles: `red-spymaster`, `blue-spymaster`, `red-operative`, `blue-operative`.

If you omit `--nickname`, the bot uses a role-based default (e.g. `RedSpymasterBot`, `BlueOperativeBot`). Logging is always at DEBUG.

The bot joins the room, waits for its role each turn, and plays until the game ends. Spymaster bots give clues on every turn; operative bots guess random tiles.

```bash
# Full automated game (4 bots) — integration test
uv run pytest packages/cno/tests/test_live_full_game.py -m integration
```

Session tokens are logged to `~/.codenames-ai/sessions.jsonl` so disconnected players can be reconnected and removed later. Ctrl+C leaves the room cleanly.

## Cluegen Package

The `cluegen` package provides offline clue generation for Codenames using semantic embeddings. It leverages a transformer model to encode words and board states, then generates the best clue for a given set of target words.

### Generating Vocabularies

Vocabularies are pre-computed word lists with associated embeddings. Generate them using the `generate_vocab.py` script:

```bash
uv run python packages/cluegen/src/cluegen/generate_vocab.py
```

This creates three vocabulary files in `packages/cluegen/data/`:
- `simple_vocab.txt` — ~5,000 common words (Zipf frequency ≥ 4.5)
- `standard_vocab.txt` — ~15,000 medium-frequency words (Zipf ≥ 3.5)
- `advanced_vocab.txt` — ~30,000+ words including less common terms (Zipf ≥ 2.5)

Vocabularies are cached as pickle files after first use, storing pre-computed embeddings for the selected model.

### Using the Spymaster Class

The `Spymaster` class generates clues by analyzing semantic relationships between board words and vocabulary candidates.

#### Basic Workflow

```python
from cluegen import Spymaster

# Initialize with an embedding model (defaults to "all-MiniLM-L6-v2")
spymaster = Spymaster(model_name="all-MiniLM-L6-v2")

# Load a vocabulary (will cache embeddings automatically)
spymaster.load_vocabulary("packages/cluegen/data/standard_vocab.txt")

# Set up the board with all 25 words
all_words = ["APPLE", "BANANA", "CARROT", ...]  # 25 words
spymaster.initialize_game_board(all_words)

# Update the board state at the start of each turn
spymaster.update_board_state(
    targets=["APPLE", "BANANA"],     # Words your team needs to guess
    civilians=["CARROT", "POTATO"],   # Neutral words
    enemies=["ORANGE", "GRAPE"],      # Opponent's words
    assassins=["POISON"]              # Lose instantly if guessed
)

# Prune vocabulary to safe, relevant words (optional but recommended)
spymaster.prune_vocabulary(danger_threshold=0.25, relevance_threshold=0.1)

# Generate a clue covering 1-3 targets
clue = spymaster.generate_clue(min_targets=1, max_targets=3)
print(f"Clue: {clue['word']} covering {clue['intended_targets']}")
```

#### Key Methods

- **`load_vocabulary(filepath)`** — Load a vocabulary file and compute/cache embeddings
- **`initialize_game_board(words)`** — Cache embeddings for the 25 board words (call once per game)
- **`update_board_state(targets, civilians, enemies, assassins)`** — Update board state at each turn
- **`prune_vocabulary(danger_threshold, relevance_threshold)`** — Filter to safe and relevant words
- **`generate_clue(min_targets, max_targets, ...)`** — Generate the best clue for current targets

#### Clue Quality Parameters

`generate_clue()` accepts tuning parameters:
- `min_targets` / `max_targets` — Range of target words to cover
- `size_bonus` — Reward for clues covering more targets (default 0.15)
- `alpha` — Penalty weight for civilian similarity (default 0.2)
- `beta` — Penalty weight for enemy similarity (default 0.4)
- `gamma` — Penalty weight for assassin similarity (default 1.0)

Higher penalties reduce false positives at the cost of fewer valid clues.

### Running the Demo

```bash
uv run python -m cluegen
```

## Tests

```bash
# Unit tests
uv run pytest -m "not integration"

# Live integration tests (network required)
uv run pytest -m integration
```
