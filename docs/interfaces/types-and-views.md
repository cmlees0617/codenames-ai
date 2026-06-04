# Types and views

**Module:** `game_core.types`, `game_core.views`

## Types

| Name | Description |
|------|-------------|
| `TeamColor` | `"red"` \| `"blue"` |
| `Role` | `"spymasters"` \| `"operatives"` |
| `TileColor` | Board bucket for algorithms: includes `"civilian"`, `"assassin"` |
| `Clue` | `word`, `count`, optional `intended_targets` (for CNO `giveClue`) |
| `GuessAction` | `GuessAction.guess(word)` or `GuessAction.end_turn()` |

## Views

| Name | Who sees it | Contents |
|------|-------------|----------|
| `SpymasterView` | Spymaster algorithms | Full board with hidden colors per card |
| `OperativeView` | Guess algorithms | Words + revealed flag only; hidden colors omitted until revealed |
| `ClueHistoryEntry` | Operatives | Past clues (`word`, `count`) |

## Wire vs domain literals

`cno_sdk.state` defines the same `TeamColor` and `Role` literals without importing `game-core`. **`cno_bots.views`** maps `GameState` into these views. Keep literals in sync when adding teams or roles.

**Source:** [`packages/game-core/src/game_core/types.py`](../../packages/game-core/src/game_core/types.py), [`views.py`](../../packages/game-core/src/game_core/views.py)
