# codenames-ai

Python tools for playing [Codenames Online](https://codenames.game): a protocol SDK, a CLI bot, and an offline clue engine.

## Layout

| Path | Description |
|------|-------------|
| `apps/cno` | Thin CLI: argparse + interactive prompts only |
| `packages/cno-bots` | CNO player bots, view adapter, match orchestration ([docs](docs/implementations/cno-bots.md)) |
| `packages/cno-sdk` | Low-level Socket.IO / boardgame.io client |
| `packages/cluegen` | `ClueAlgorithm` / `GuessAlgorithm` implementations |
| `packages/game-core` | Role views, types, and player/algorithm protocols |

**Contributor documentation:** [docs/index.md](docs/index.md) (MkDocs). Local preview: `uv run mkdocs serve`. Covers architecture, interfaces, contributor guides, CLI reference, ADRs, and selective API docs.

## Requirements

- Python 3.12+
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

# Spymaster: pick from top 10 ranked clues
uv run cno halok-jonah red-spymaster --interactive

# Operative: random guesses instead of embeddings
uv run cno halok-jonah blue-operative --random-operative
```

Roles: `red-spymaster`, `blue-spymaster`, `red-operative`, `blue-operative`.

If you omit `--nickname`, the bot uses a role-based default (e.g. `RedSpymasterBot`, `BlueOperativeBot`). Logging is always at DEBUG.

Spymaster bots use `CluegenClueAlgorithm` (auto or interactive). Operative bots use `EmbeddingGuessAlgorithm` by default.

```bash
# Full automated game (4 bots) — integration test
uv run pytest apps/cno/tests/test_live_full_game.py -m integration
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

### Using ClueEngine (offline)

The internal `ClueEngine` class searches vocabulary for clues. Live play uses `CluegenClueAlgorithm` via `cno-bots` (see [docs](docs/README.md)).

#### Basic Workflow

```python
from cluegen import ClueEngine

engine = ClueEngine(model_name="all-MiniLM-L6-v2")
engine.load_vocabulary("packages/cluegen/data/standard_vocab.txt")

all_words = ["APPLE", "BANANA", "CARROT", ...]  # 25 words
engine.initialize_game_board(all_words)

engine.update_board_state(
    targets=["APPLE", "BANANA"],
    civilians=["CARROT", "POTATO"],
    enemies=["ORANGE", "GRAPE"],
    assassins=["POISON"],
)

engine.prune_vocabulary(danger_threshold=0.25, relevance_threshold=0.1)
clue = engine.generate_clue(min_targets=1, max_targets=3)
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

## Tests, lint, and docs

```bash
uv sync --all-packages --group dev

# Unit tests
uv run pytest -m "not integration"

# Ruff (Python 3.12 + UP) and mypy (strict on game-core, cno-bots, cno, cluegen.algorithms)
uv run ruff check apps packages
uv run mypy -p game_core -p cno_bots -p cno -p cluegen.algorithms

# Contributor docs (MkDocs + Material + mkdocstrings + Mermaid)
uv run mkdocs serve

# Live integration tests (network required)
uv run pytest -m integration
```
