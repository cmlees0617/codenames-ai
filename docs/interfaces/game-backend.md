# GameBackend (planned)

**Module:** `game_core.backends`  
**Protocol:** `@runtime_checkable`  
**Status:** Defined only — **no implementation** yet.

## Purpose

Abstract async transport for a Codenames room so [`SpymasterPlayer`](spymaster-player.md) and [`OperativePlayer`](operative-player.md) can run against backends other than codenames.game.

Today, [`CNOSpymasterBot`](../implementations/cno-bots.md) and [`CNOOperativeBot`](../implementations/cno-bots.md) call `CNOClient` directly.

## Contract (sketch)

| Method | Role |
|--------|------|
| `connect` | Join transport / room |
| `join(team, role)` | Seat player |
| `wait_for_spymaster_turn` | Return `SpymasterView` |
| `wait_for_operative_turn` | Return `OperativeView` |
| `submit_clue` | Apply spymaster move |
| `submit_guess` | Guess or pass |
| `disconnect` | Cleanup |
| `gameover` | Winner or `None` |

When a second backend is added, implement `GameBackend` in its package and refactor CNO bots to accept a backend instance.

**Source:** [`backends.py`](https://github.com/cmlees0617/codenames-ai/blob/main/packages/game-core/src/game_core/backends.py)
