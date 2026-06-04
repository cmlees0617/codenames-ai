# OperativePlayer

**Module:** `game_core.players`  
**Protocol:** `@runtime_checkable`

## Contract

```python
async def play(self) -> str: ...
async def close(self) -> None: ...
```

- **`play`:** Connect, join as operative, wait for turns, call [`GuessAlgorithm`](guess-algorithm.md) each guess until the phase ends.
- **`close`:** Leave the room.

## CNO implementation

| Class | Package |
|-------|---------|
| `CNOOperativeBot` | `cno_bots.bots.operative` |

**Source:** [`players.py`](https://github.com/cmlees0617/codenames-ai/blob/main/packages/game-core/src/game_core/players.py)
