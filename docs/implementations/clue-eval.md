# clue-eval

**Path:** `packages/clue-eval`

## Purpose

**Predefined clue tests** and a **model-agnostic harness** for running any [`ClueAlgorithm`](../interfaces/clue-algorithm.md) through them.

Contributors implement `ClueAlgorithm`, then run the repo catalog—they are **not** scored against another algorithm in the monorepo (including `cluegen`).

Depends on **`game-core` only**.

## Layout

```text
packages/clue-eval/
  data/                    # test_boards.json, words.txt, future case data
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

## Optional example package

[`cluegen`](cluegen.md) ships an embedding-based `ClueAlgorithm` you can study or use in live bots. Evaluating it means running the **same** `default_suite()` with `CluegenClueAlgorithm()`—not a separate benchmark path.
