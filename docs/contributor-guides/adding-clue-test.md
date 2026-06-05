# Add benchmark boards

## Problem

Spymaster benchmarks need **reproducible board sets** with stratified difficulty. Board data and generation live in `clue-eval`, not in `cluegen` or algorithm packages.

## When to use

- Regenerate or resize the standard benchmark file
- Add a custom board JSON for an experiment
- Tune difficulty stratification (`beta`, candidate pool size, etc.)

## Steps

### 1. Regenerate the standard 5000-board set

From the repository root:

```bash
uv sync --package clue-eval --extra embeddings
uv run python packages/clue-eval/examples/generate_standard_board_set.py
```

Options: `-n` / `--count`, `-o` / `--output`, `--seed`, `--beta`. See the script help.

### 2. Generate a smaller custom set in code

```python
from pathlib import Path

from clue_eval.boards import BoardFactory
from clue_eval.embeddings import EmbeddingStore

store = EmbeddingStore.load()
BoardFactory.generate_and_save_uniform_difficulty_boards(
    100,
    store,
    Path("my_boards.json"),
    seed=42,
    beta=2.0,
)
```

Saved JSON is ordered **easiest → hardest** with `id` reassigned and optional `difficulty: {blue, red}` per board.

### 3. Add static fixture boards

Drop a JSON array into `packages/clue-eval/data/` and load with `load_boards_from_json`. Use the same layout keys as `BoardLayout` (`blues`, `reds`, `civilians`, `assassins`).

## Related

- [clue-eval implementation](../implementations/clue-eval.md)
- [ADR-0004](../adrs/0004-clue-eval-catalog.md)
