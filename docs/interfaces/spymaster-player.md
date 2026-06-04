# SpymasterPlayer

**Module:** `game_core.players`  
**Protocol:** `@runtime_checkable`

## Contract

```python
async def play(self) -> str: ...
async def close(self) -> None: ...
```

- **`play`:** Connect (if needed), join as spymaster, wait for turns, submit clues until `gameover`. Returns room slug.
- **`close`:** Leave the room and release resources.

Uses a [`ClueAlgorithm`](clue-algorithm.md) internally; does not expose algorithm choice in the protocol.

## CNO implementation

| Class | Package |
|-------|---------|
| `CNOSpymasterBot` | `cno_bots.bots.spymaster` |

Constructor accepts optional `select_clue` callback (provided by the CLI for interactive play).

**Source:** [`players.py`](https://github.com/cmlees0617/codenames-ai/blob/main/packages/game-core/src/game_core/players.py)
