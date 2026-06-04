# Testing and quality

## Unit tests (CI default)

```bash
uv run pytest -m "not integration"
```

| Package | Path | Focus |
|---------|------|-------|
| `game-core` | `packages/game-core/tests` | Types, protocols |
| `cluegen` | `packages/cluegen/tests` | Engines + algorithms (mocked ML) |
| `cno-sdk` | `packages/cno-sdk/tests` | Protocol parsing, fixtures |
| `cno-bots` | `packages/cno-bots/tests` | View mapping, protocols |
| `cno` | `apps/cno/tests` | Argparse, interactive wiring |

## Integration tests

```bash
uv run pytest -m integration
```

- Live codenames.game (network required)
- Heavy `CluegenClueAlgorithm` fixture test
- `run_full_game` uses scripted algorithms — no random ML in the default live path

## Lint and types

```bash
uv run ruff check apps packages
uv run mypy -p game_core -p cno_bots -p cno -p cluegen.algorithms
```

**Note:** Legacy `ClueEngine` / `GuessEngine` modules are excluded from strict mypy until typed. See `pyproject.toml` overrides.

## Protocol conformance

Use `@runtime_checkable` checks in tests:

```python
assert isinstance(algo, ClueAlgorithm)
```

See `packages/cno-bots/tests/test_protocols.py`.

## When you add an extension point

1. Unit test the algorithm with constructed views (no network).
2. Add a scripted implementation for integration tests if needed.
3. Update interface doc if behavior or invariants change.
