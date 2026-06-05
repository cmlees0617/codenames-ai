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

## Full-game benchmark (5000 boards × 3 operatives)

`CluegenClueAlgorithm` implements [`ClueAlgorithm`](../interfaces/clue-algorithm.md) via
``rank_clues(state: SpymasterView, *, limit=10) -> list[Clue]`` and sets ``name = "cluegen"`` for
result files under ``packages/clue-eval/data/results/``.

From the repository root (installs cluegen, GloVe operatives, and optional LLM operative):

```bash
uv sync --all-packages
uv sync --package clue-eval --extra embeddings --extra llm
uv run python packages/clue-eval/examples/run_spymaster_simulation.py --cluegen
```

Equivalent explicit import:

```bash
uv run python packages/clue-eval/examples/run_spymaster_simulation.py \
  --spymaster-module cluegen.algorithms.clue:CluegenClueAlgorithm
```

Debug run (one operative, first N boards):

```bash
uv run python packages/clue-eval/examples/run_spymaster_simulation.py \
  --cluegen --operative static_embedding --sample 25
```

Sanity check (operative uses the same ``all-MiniLM-L6-v2`` embeddings as cluegen):

```bash
uv sync --package clue-eval --extra cluegen
uv run python packages/clue-eval/examples/run_spymaster_simulation.py \
  --cluegen --operative cluegen_embedding --sample 100
```

Smoke run (30 games, three progress bars):

```bash
uv run python packages/clue-eval/examples/run_spymaster_simulation.py --cluegen --sample 10
```

Outputs:

- ``cluegen_static_embedding.json``
- ``cluegen_softmax_embedding.json``
- ``cluegen_llm.json``

The first ``rank_clues`` call loads vocabulary and embeddings; the full 15k-game run can take a long time.

**Embedding operatives** embed clues in the full GloVe model, then rank guesses among the 400
Codenames board words. Cluegen + ``static_embedding`` is a valid pairing; only clues with no GloVe
vector at all are skipped.

See [clue-eval simulation](clue-eval.md#full-game-spymaster-simulation-5000-boards).
