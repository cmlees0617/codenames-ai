# apps/cno (CLI)

**Path:** [`apps/cno`](https://github.com/cmlees0617/codenames-ai/tree/main/apps/cno)

## Responsibility

Thin entrypoint only:

| Module | Purpose |
|--------|---------|
| `cno.cli` | `argparse`, `main`, wires `cno_bots` |
| `cno.interactive` | questionary prompts, `prompt_select_clue` |
| `cno.roles` | Parse `red-spymaster` etc. |

## Command

```bash
uv run cno [room] [role] [--interactive] [--random-operative]
```

## Flow

1. Parse or prompt for args
2. `build_player(PlayerBuildOptions(...))`
3. `run_player(player)`

No game logic in this package.

**Script:** `cno = cno.cli:main` in [`apps/cno/pyproject.toml`](https://github.com/cmlees0617/codenames-ai/blob/main/apps/cno/pyproject.toml)
