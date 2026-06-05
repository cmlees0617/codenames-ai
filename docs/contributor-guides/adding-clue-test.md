# Add benchmark boards and catalog tests

## Benchmark boards (stable)

Spymaster benchmarks need **reproducible board sets** with stratified difficulty. Board data and generation live in `clue-eval`, not in `cluegen` or algorithm packages.

### When to use

- Regenerate or resize the standard benchmark file
- Add a custom board JSON for an experiment
- Tune difficulty stratification (`beta`, candidate pool size, etc.)

### Regenerate the standard 5000-board set

From the repository root:

```bash
uv sync --package clue-eval --extra embeddings
uv run python packages/clue-eval/examples/generate_standard_board_set.py
```

Options: `-n` / `--count`, `-o` / `--output`, `--seed`, `--beta`. See the script help.

### Generate a smaller custom set in code

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

### Add static fixture boards

Drop a JSON array into `packages/clue-eval/data/` and load with `load_boards_from_json`. Use the same layout keys as `BoardLayout` (`blues`, `reds`, `civilians`, `assassins`).

---

## Predefined catalog tests (`feature/spymaster-test-pipeline`)

!!! warning "Test pipeline in progress"
    This branch also adds a full-game benchmark harness that is **experimental** and likely to be massively reworked. The **catalog** steps below are relatively stable; see [clue-eval](../implementations/clue-eval.md) for the WIP simulation path.

Contributors need a **shared catalog** of boards and expectations so every `ClueAlgorithm` is judged the same way.

### When to use

- New fixture board or regression case for the catalog
- New ground-truth targets or tags for benchmarking

### Register a `ClueTest`

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

### Run the catalog

```python
from clue_eval import SuiteRunner, default_suite

SuiteRunner(MyClueAlgorithm()).run_suite(default_suite())
```

`ClueTest` is the extension point for non-target checks (clue legality, assassin proximity, etc.) without coupling to any one ML implementation.

## Related

- [clue-eval implementation](../implementations/clue-eval.md)
- [ADR-0004](../adrs/0004-clue-eval-catalog.md)
