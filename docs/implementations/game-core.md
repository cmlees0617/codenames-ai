# game-core

**Path:** [`packages/game-core`](../../packages/game-core)

## Responsibility

Domain layer only:

- Types and views ([interfaces](../interfaces/types-and-views.md))
- [`ClueAlgorithm`](../interfaces/clue-algorithm.md), [`GuessAlgorithm`](../interfaces/guess-algorithm.md)
- [`SpymasterPlayer`](../interfaces/spymaster-player.md), [`OperativePlayer`](../interfaces/operative-player.md)
- [`GameBackend`](../interfaces/game-backend.md) (stub)

## Must not

- Import `cno-sdk` or `cluegen`
- Perform I/O or load ML models

## Tests

`packages/game-core/tests/`
