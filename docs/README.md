# Documentation

Reference for interfaces (contracts) and implementations in this monorepo.

## Interfaces (`game-core`)

| Doc | Symbol | Purpose |
|-----|--------|---------|
| [clue-algorithm.md](interfaces/clue-algorithm.md) | `ClueAlgorithm` | Rank candidate clues from a spymaster view |
| [guess-algorithm.md](interfaces/guess-algorithm.md) | `GuessAlgorithm` | Choose one guess or pass from an operative view |
| [spymaster-player.md](interfaces/spymaster-player.md) | `SpymasterPlayer` | Async loop for the spymaster role |
| [operative-player.md](interfaces/operative-player.md) | `OperativePlayer` | Async loop for the operative role |
| [game-backend.md](interfaces/game-backend.md) | `GameBackend` | Future: abstract room transport (not wired for CNO yet) |
| [types-and-views.md](interfaces/types-and-views.md) | `Clue`, views, literals | Shared domain snapshots |

## Implementations

| Doc | Package | Role |
|-----|---------|------|
| [game-core.md](implementations/game-core.md) | `game-core` | Protocols and domain types only |
| [cluegen.md](implementations/cluegen.md) | `cluegen` | Algorithm + internal ML engines |
| [cno-sdk.md](implementations/cno-sdk.md) | `cno-sdk` | codenames.game wire client |
| [cno-bots.md](implementations/cno-bots.md) | `cno-bots` | CNO player bots and orchestration |
| [cno-cli.md](implementations/cno-cli.md) | `apps/cno` | CLI and interactive UI |

## Architecture

See [../ARCHITECTURE.md](../ARCHITECTURE.md) for dependency rules and layer boundaries.
