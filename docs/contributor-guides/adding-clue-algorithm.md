# Add a clue algorithm

## Problem

Spymaster bots need ranked clue candidates from the current board without coupling to Socket.IO. `ClueAlgorithm` isolates that decision.

## When to use

- New heuristic, LLM, or search strategy for clues
- A/B testing clue quality offline before live play

Do **not** implement turn waiting or `give_clue` here — that belongs in `CNOSpymasterBot` (or a future `GameBackend`).

## Contract

Implement [`ClueAlgorithm`](../interfaces/clue-algorithm.md):

```python
def rank_clues(self, state: SpymasterView, *, limit: int = 10) -> list[Clue]:
```

**Invariants:**

- Pure function of `SpymasterView` (no I/O in `rank_clues`)
- Return best clues first; may return fewer than `limit`
- Use `Clue(word=..., count=..., intended_targets=...)`; `count` is operative-facing

## Steps

### 1. Add a class in `cluegen` (typical)

Create `packages/cluegen/src/cluegen/algorithms/my_clue.py` (or another package if it has no ML deps and only depends on `game-core`).

```python
from game_core.types import Clue
from game_core.views import SpymasterView

class MyClueAlgorithm:
    def rank_clues(self, state: SpymasterView, *, limit: int = 10) -> list[Clue]:
        ...
```

Export from `cluegen.algorithms.__init__` if it should ship with the package.

### 2. Register for bots or tests

**Factory (default live path):** extend `cno_bots.factory._build_spymaster` if this should replace `CluegenClueAlgorithm`, or add a factory option / env flag.

**Tests:** use `ScriptedClueAlgorithm` as a template, or unit-test `rank_clues` with a minimal `SpymasterView` (see `packages/cluegen/tests/test_algorithms.py`). For the repo catalog, use `SuiteRunner` + `default_suite()` from [clue-eval](../implementations/clue-eval.md)—you are graded against predefined cases, not against `cluegen`.

### 3. Document

- Update [cluegen implementation](../implementations/cluegen.md) table
- Add mkdocstrings entry in [api/cluegen.md](../api/cluegen.md) if exported publicly

## Example: minimal test double

```python
from game_core.types import Clue
from game_core.views import SpymasterBoardCard, SpymasterView

class AlwaysOcean:
    def rank_clues(self, state: SpymasterView, *, limit: int = 10) -> list[Clue]:
        targets = tuple(
            c.word for c in state.board
            if c.color == state.team and not c.revealed
        )[:3]
        return [Clue("OCEAN", len(targets), intended_targets=targets)]
```

## Reuse internal `ClueEngine`

For embedding-based search, wrap [`ClueEngine`](../implementations/cluegen.md) like `CluegenClueAlgorithm` does — do not fork vocabulary loading unless necessary.

## Related

- [ClueAlgorithm interface](../interfaces/clue-algorithm.md)
- [Execution flow — spymaster turn](../architecture/execution-flow.md)
