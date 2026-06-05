# cluegen (example package)

**Path:** `packages/cluegen`

## Role

**Optional example** of embedding-based clue and guess logic. Helpful for demos and as a default in `cno-bots`, but **not required** by `clue-eval`, `game-core`, or live play.

## Public API

### Algorithms (`game-core` protocols)

| Class | Protocol |
|-------|----------|
| `CluegenClueAlgorithm` | `ClueAlgorithm` (wraps `ClueEngine`) |
| `EmbeddingGuessAlgorithm` | `GuessAlgorithm` |
| `RandomGuessAlgorithm` | `GuessAlgorithm` |
| `ScriptedClueAlgorithm` / `ScriptedGuessAlgorithm` | Tests |

### Internal engines

| Class | Module | Role |
|-------|--------|------|
| `ClueEngine` | `cluegen.clue_engine` | Vocab + embeddings |
| `EmbeddingGuessEngine` / `LLMGuessEngine` | `cluegen.guess_engine` | Offline guess demos |

`CluegenClueAlgorithm(..., prune_vocabulary=True)` controls embedding-specific pruning.

### Visualization

`cluegen.viz.plot_board_and_clue` — debugging plots for `ClueEngine` only.

## Data

Vocabulary under `packages/cluegen/data/`. Benchmark boards for difficulty scoring live in **`clue-eval/data/`** (see [clue-eval](clue-eval.md)).

## Example demo

```bash
uv run python -m cluegen
```

## Live bots

`cno_bots.factory` defaults to `CluegenClueAlgorithm` / `EmbeddingGuessAlgorithm` but accepts overrides:

```python
PlayerBuildOptions(..., clue_algorithm=MyClueAlgorithm())
```

## Testing your algorithm

Unit-test `rank_clues` with constructed `SpymasterView` objects (see `packages/cluegen/tests/test_algorithms.py`). Use benchmark boards from [clue-eval](clue-eval.md) when you need fixed layouts with difficulty metadata.
