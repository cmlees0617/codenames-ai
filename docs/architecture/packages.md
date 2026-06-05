# Packages and boundaries

## Workspace members

| Package | Path | Responsibility |
|---------|------|----------------|
| `game-core` | `packages/game-core` | Domain types, role views, `Protocol`s |
| `clue-eval` | `packages/clue-eval` | Benchmark boards (+ catalog & WIP test pipeline on feature branch) |
| `cluegen` | `packages/cluegen` | Optional example embedding algorithms (not required by eval) |
| `cno-sdk` | `packages/cno-sdk` | codenames.game Socket.IO client, `GameState` parsing |
| `cno-bots` | `packages/cno-bots` | View adapter, `CNOSpymasterBot`, `CNOOperativeBot`, `run_full_game` |
| `cno` | `apps/cno` | `cno` console script — prompts and argparse only |

Root `pyproject.toml` defines the uv workspace (`apps/*`, `packages/*`) and shared dev tooling.

## What belongs where

### game-core

**Solves:** Stable contracts between algorithms and players without tying to wire format.

**Contains:** `Clue`, `GuessAction`, `SpymasterView`, `OperativeView`, `ClueAlgorithm`, `GuessAlgorithm`, `SpymasterPlayer`, `OperativePlayer`, `GameBackend` (stub).

**Does not contain:** HTTP, sockets, ML models, or argparse.

### clue-eval

**Solves:** Produce reproducible board sets with per-team difficulty (stable on `main`). On `feature/spymaster-test-pipeline`, also evaluate `ClueAlgorithm` implementations via a catalog and an in-progress full-game spymaster benchmark.

!!! warning "Pipeline in progress"
    Only the simulation harness (operative agents, game loop, result JSON) is unstable and likely to be massively reworked. Board generation is stable.

**Contains:** `BoardFactory`, `board_difficulty`, `EmbeddingStore`, `generate_standard_board_set.py`, `board_layout_to_spymaster_view`; on the feature branch—`SuiteRunner` / `ScenarioRunner`, clue legality, operative test conditions, `simulation` runners, `run_spymaster_simulation.py`.

**May import:** `game-core`, `numpy`, `tqdm`, optional `gensim` / `transformers` / `sentence-transformers`. **Must not import:** `cluegen`, `cno-sdk`, `cno-bots`, `apps/cno`.

### cluegen (optional example)

**Solves:** Example embedding spymaster/guesser code; convenient defaults for `cno-bots` demos.

**Contains:** `ClueEngine`, `CluegenClueAlgorithm`, `EmbeddingGuessAlgorithm`, `Scripted*` algorithms, `cluegen.viz`.

**May import:** `game-core` only. **Must not import:** `clue-eval`, `cno-sdk`, `cno-bots`, `apps/cno`.

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
- [clue-eval](../implementations/clue-eval.md)
- [cno-sdk](../implementations/cno-sdk.md)
- [cno-bots](../implementations/cno-bots.md)
- [CLI](../implementations/cno-cli.md)
