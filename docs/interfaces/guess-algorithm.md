# GuessAlgorithm

**Module:** `game_core.algorithms`  
**Protocol:** `@runtime_checkable`

## Contract

```python
def guess_word(self, state: OperativeView) -> GuessAction:
```

- **Input:** [`OperativeView`](types-and-views.md) including `current_clue`, `guesses_remaining`, and public board.
- **Output:** One [`GuessAction`](types-and-views.md): a word to guess or end the guessing phase.
- **Sync only** — called once per guess; `CNOOperativeBot` loops until the turn ends.

## Implementations

| Class | Package | Notes |
|-------|---------|-------|
| `EmbeddingGuessAlgorithm` | `cluegen.algorithms` | One guess at a time via [`EmbeddingGuessEngine`](../implementations/cluegen.md) |
| `RandomGuessAlgorithm` | `cluegen.algorithms` | Random unrevealed tile |
| `ScriptedGuessAlgorithm` | `cluegen.algorithms` | Queued guesses for tests |

**Source:** [`packages/game-core/src/game_core/algorithms.py`](../../packages/game-core/src/game_core/algorithms.py)
