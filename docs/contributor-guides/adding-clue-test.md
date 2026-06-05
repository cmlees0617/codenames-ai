# Add a predefined clue test

!!! warning "Test pipeline in progress"
    Branch `feature/spymaster-test-pipeline` also adds a full-game benchmark harness that is **experimental** and likely to be massively reworked. This guide covers the **catalog** (`ClueTest` / `SuiteRunner`); see [clue-eval](../implementations/clue-eval.md) for the WIP simulation path.

## Problem

Contributors need a **shared catalog** of boards and expectations so every `ClueAlgorithm` is judged the same way. Tests live in `clue-eval`, not in `cluegen` or algorithm packages.

## When to use

- New fixture board or regression case for the catalog
- New ground-truth targets or tags for benchmarking

## Steps

### 1. Add board data (if needed)

- Drop JSON into `packages/clue-eval/data/`, or
- Build layouts with `BoardFactory` inside catalog code

### 2. Register a `ClueTest`

Edit `packages/clue-eval/src/clue_eval/suite/catalog.py`:

```python
ClueTest(
    id="my-case-1",
    description="What this case checks",
    scenario=Scenario(
        name="my-case-1",
        board={...},
        team="blue",
        expected_targets=frozenset({"WORD"}),  # optional
    ),
    tags=frozenset({"regression"}),
)
```

Include the test in `default_suite()` or a new `TestSuite` returned from `all_suites()`.

### 3. Run the catalog

```python
from clue_eval import SuiteRunner, default_suite

SuiteRunner(MyClueAlgorithm()).run_suite(default_suite())
```

## Future assertions

`ClueTest` is the extension point for non-target checks (clue legality, assassin proximity, etc.) without coupling to any one ML implementation.

## Related

- [clue-eval implementation](../implementations/clue-eval.md)
- [ADR-0004](../adrs/0004-clue-eval-catalog.md)
