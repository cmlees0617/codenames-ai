# ClueAlgorithm

**Module:** `game_core.algorithms`  
**Protocol:** `@runtime_checkable`

## Contract

```python
def rank_clues(self, state: SpymasterView, *, limit: int = 10) -> list[Clue]:
```

- **Input:** [`SpymasterView`](types-and-views.md) for the bot’s team.
- **Output:** Clues ordered best-first. Empty list if no legal clue.
- **Sync only** — no network or filesystem I/O in the protocol.

Bots (e.g. `CNOSpymasterBot`) decide how to pick from the list (auto: first item; CLI: human picks from top N).

## Implementations

| Class | Package | Notes |
|-------|---------|-------|
| `CluegenClueAlgorithm` | `cluegen.algorithms` | Optional example; embeddings via [`ClueEngine`](../implementations/cluegen.md) |
| `ScriptedClueAlgorithm` | `cluegen.algorithms` | Fixed clues for tests |

**Source:** [`algorithms.py`](https://github.com/cmlees0617/codenames-ai/blob/main/packages/game-core/src/game_core/algorithms.py)
