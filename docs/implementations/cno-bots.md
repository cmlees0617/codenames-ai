# cno-bots

**Path:** [`packages/cno-bots`](https://github.com/cmlees0617/codenames-ai/tree/main/packages/cno-bots)

## Responsibility

Codenames Online player layer:

| Module | Purpose |
|--------|---------|
| `cno_bots.views` | `GameState` → `SpymasterView` / `OperativeView` |
| `cno_bots.bots` | `CNOSpymasterBot`, `CNOOperativeBot` |
| `cno_bots.factory` | `build_player(PlayerBuildOptions)` |
| `cno_bots.runner` | `run_player`, `ShutdownController` |
| `cno_bots.game` | `run_full_game` (four bots) |
| `cno_bots.browser_game` | Two spymaster bots + human operatives in browser |

## Must not

- Import `questionary` or parse CLI role strings

Interactive clue selection is injected via `select_clue` from [`apps/cno`](cno-cli.md).

## Factory

```python
PlayerBuildOptions(team, role, room, nickname, random_operative=False, select_clue=None)
build_player(options) -> SpymasterPlayer | OperativePlayer
```
