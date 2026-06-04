# Packages and boundaries

## Workspace members

| Package | Path | Responsibility |
|---------|------|----------------|
| `game-core` | `packages/game-core` | Domain types, role views, `Protocol`s |
| `cluegen` | `packages/cluegen` | Algorithm implementations + `ClueEngine` / `GuessEngine` ML |
| `cno-sdk` | `packages/cno-sdk` | codenames.game Socket.IO client, `GameState` parsing |
| `cno-bots` | `packages/cno-bots` | View adapter, `CNOSpymasterBot`, `CNOOperativeBot`, `run_full_game` |
| `cno` | `apps/cno` | `cno` console script — prompts and argparse only |

Root `pyproject.toml` defines the uv workspace (`apps/*`, `packages/*`) and shared dev tooling.

## What belongs where

### game-core

**Solves:** Stable contracts between algorithms and players without tying to wire format.

**Contains:** `Clue`, `GuessAction`, `SpymasterView`, `OperativeView`, `ClueAlgorithm`, `GuessAlgorithm`, `SpymasterPlayer`, `OperativePlayer`, `GameBackend` (stub).

**Does not contain:** HTTP, sockets, ML models, or argparse.

### cluegen

**Solves:** Reusable clue/guess logic for offline tests and live bots.

**Contains:** `CluegenClueAlgorithm`, `EmbeddingGuessAlgorithm`, test `Scripted*` algorithms, internal `ClueEngine` / `EmbeddingGuessEngine`.

**Does not contain:** Room slugs, `CNOClient`, or CLI strings like `red-spymaster`.

### cno-sdk

**Solves:** Speak boardgame.io / Socket.IO to codenames.game.

**Contains:** `CNOClient`, move builders, patch application, session log.

**Does not contain:** Clue ranking or guess heuristics.

### cno-bots

**Solves:** Run one bot role in a CNO room until game over.

**Contains:** `build_player`, turn loops, `to_spymaster_view` / `to_operative_view`.

**Does not contain:** questionary menus (CLI injects `select_clue` only).

### apps/cno

**Solves:** Operator entrypoint for development and demos.

**Contains:** `main()`, `prompt_interactive`, `prompt_select_clue`, role string parsing.

**Does not contain:** `generate_clue` or embedding models.

## Intentional duplication

`TeamColor` and `Role` literals exist in both `cno_sdk.state` and `game_core.types` so the SDK never depends on `game-core`. Values must stay identical; the adapter is `cno_bots.views`. See [ADR-0003](../adrs/0003-wire-domain-literals.md).

## Implementation summaries

- [game-core](../implementations/game-core.md)
- [cluegen](../implementations/cluegen.md)
- [cno-sdk](../implementations/cno-sdk.md)
- [cno-bots](../implementations/cno-bots.md)
- [CLI](../implementations/cno-cli.md)
