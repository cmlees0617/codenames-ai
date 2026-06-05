# Contributor guides

Task-oriented guides for extending the system. Read [Architecture overview](../architecture/overview.md) first.

| Guide | You will… |
|-------|-----------|
| [Add a clue algorithm](adding-clue-algorithm.md) | Implement `ClueAlgorithm` and wire it into `build_player` or tests |
| [Add benchmark boards](adding-clue-test.md) | Generate or extend `clue-eval` board sets |
| [Add a guess algorithm](adding-guess-algorithm.md) | Implement `GuessAlgorithm` for operative bots |
| [Add a game backend](adding-game-backend.md) | Plan a non-CNO implementation using `GameBackend` |
| [Extend the CLI](extending-cli.md) | Add flags, prompts, or selection strategies |
| [Testing & quality](testing.md) | Run pytest, ruff, mypy, and integration tests |

## Checklist for any change

1. Identify the **extension point** (`Protocol` or factory option).
2. Add or update the [interface](../interfaces/clue-algorithm.md) narrative if the contract changes.
3. Update Mermaid diagrams if package boundaries or flow change.
4. Add an [ADR](../adrs/index.md) for non-obvious design choices.
5. Extend [API reference](../api/index.md) only for public contributor-facing symbols.
6. Run [Testing & quality](testing.md) before opening a PR.
