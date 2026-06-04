# clue-eval

**Path:** `packages/clue-eval`

## Purpose

**Predefined clue tests** and a **model-agnostic harness** for running any [`ClueAlgorithm`](../interfaces/clue-algorithm.md) through them.

Contributors implement `ClueAlgorithm`, then run the repo catalog—they are **not** scored against another algorithm in the monorepo (including `cluegen`).

Depends on **`game-core` only**.

## Layout

```text
packages/clue-eval/
  data/                    # test_boards.json, words.txt, glove-wiki-gigaword-300.npz
  src/clue_eval/
    boards/                # layouts, factory, SpymasterView conversion
    scenarios/             # Scenario + ScenarioRunner
    suite/                 # ClueTest, TestSuite, catalog, SuiteRunner
    benchmark/             # timing / summary printing
    demos/                 # StubClueAlgorithm for CI smoke
  tests/
```

## Predefined catalog

| Type | Role |
|------|------|
| `ClueTest` | One catalog entry (`id`, `Scenario`, description, tags) |
| `TestSuite` | Named list of tests |
| `default_suite()` | Shipped starter catalog (fixture boards today; more cases TBD) |

Add cases in `clue_eval.suite.catalog` (or JSON loaders) as requirements grow—legality checks, assassin safety, etc. can hang off `ClueTest` later.

## Usage

```python
from clue_eval import SuiteRunner, default_suite
from my_package import MyClueAlgorithm

results = SuiteRunner(MyClueAlgorithm()).run_suite(default_suite())
```

Smoke run (stub algorithm, no ML):

```bash
uv run python -m clue_eval --stub
```

## Scenario fields (model-agnostic)

| Field | Meaning |
|-------|---------|
| `board` | Tile layout (`blues` / `reds` / … are colors on the board) |
| `team` | Spymaster's team |
| `clue_limit` | `rank_clues(..., limit=...)` |
| `expected_targets` | Optional pass/fail on top clue's `intended_targets` |

Algorithm-specific options (e.g. vocabulary pruning) live on **your** implementation, not on `Scenario`.

## Board difficulty and stratified generation

Per-team difficulty (GloVe cosine similarity, default ``beta=2.0``):

```text
difficulty = avg_sim(targets, targets)
             / (avg_sim(targets, others) + beta * max_sim(targets, assassin))
```

- **Blue** targets = ``blues``; others = ``reds`` + ``civilians`` + ``assassins``
- **Red** targets = ``reds``; others = ``blues`` + ``civilians`` + ``assassins``

``FixtureBoard`` may include ``difficulty: {"blue": float, "red": float}``.

Generate ``n`` boards with evenly spaced mean difficulty:

```python
from clue_eval.embeddings import EmbeddingStore
from clue_eval.boards import BoardFactory

store = EmbeddingStore.load()
boards = BoardFactory.generate_uniform_difficulty_boards(10, store, seed=0)
```

## Word embeddings (GloVe)

The Codenames word list (`data/words.txt`, 400 words) has precomputed **glove-wiki-gigaword-300** vectors in `data/glove-wiki-gigaword-300.npz` (300 dimensions). GloVe is a strong static baseline for word similarity; it is not contextual like sentence-transformers.

Regenerate after changing `words.txt`:

```bash
uv sync --package clue-eval --extra embeddings
uv run --extra embeddings clue-eval-embed
# or: uv run --extra embeddings python -m clue_eval.embeddings
```

Load in code:

```python
from clue_eval.embeddings import EmbeddingStore

store = EmbeddingStore.load()
vec = store.vector_for("APPLE")
```

## Optional example package

[`cluegen`](cluegen.md) ships an embedding-based `ClueAlgorithm` you can study or use in live bots. Evaluating it means running the **same** `default_suite()` with `CluegenClueAlgorithm()`—not a separate benchmark path.
