# cluegen (example package)

**Path:** `packages/cluegen`

## Role

**Optional example** of embedding-based clue and guess logic. Helpful for demos and as a default in `cno-bots`, but **not required** by `clue-eval`, `game-core`, or the predefined test catalog.

Implement your own `ClueAlgorithm` and run [`clue-eval`](clue-eval.md) to validate against repo tests.

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

`CluegenClueAlgorithm(..., prune_vocabulary=True)` controls embedding-specific pruning—not part of `clue-eval` scenarios.

### Visualization

`cluegen.viz.plot_board_and_clue` — debugging plots for `ClueEngine` only.

## Data

Vocabulary under `packages/cluegen/data/`. Evaluation boards live in **`clue-eval/data/`**.

## Example demo

```bash
uv run python -m cluegen
```

## Live bots

`cno_bots.factory` defaults to `CluegenClueAlgorithm` / `EmbeddingGuessAlgorithm` but accepts overrides:

```python
PlayerBuildOptions(..., clue_algorithm=MyClueAlgorithm())
```

## Evaluate against repo tests

Same path as any other algorithm:

```python
from clue_eval import SuiteRunner, default_suite
from cluegen.algorithms import CluegenClueAlgorithm

SuiteRunner(CluegenClueAlgorithm()).run_suite(default_suite())
```
