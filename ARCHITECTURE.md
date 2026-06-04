# Architecture and layer boundaries

## Package layers

| Layer | Package | Responsibility | Must not |
|-------|---------|----------------|----------|
| Wire | `cno-sdk` | Socket.IO, BGIO state parsing, moves | Import `game-core` or `cluegen` |
| Domain | `game-core` | Role views, `Clue`/`GuessAction`, algorithm and player **protocols** | Import `cno-sdk`, do I/O, or load ML models |
| Algorithms | `cluegen` | `ClueAlgorithm` / `GuessAlgorithm` implementations (embeddings, vocab) | Import `cno-sdk` or know about rooms/clients |
| CNO players | `cno-bots` | Map `GameState` → views; `CNOSpymasterBot` / `CNOOperativeBot`; match orchestration | Import `questionary` or parse CLI strings |
| CLI | `apps/cno` | `argparse`, interactive prompts, invoke `cno_bots.factory` | Implement game loops or clue/guess logic |

```text
apps/cno (CLI)
    → cno-bots (CNO adapter + bots)
        → cno-sdk, game-core, cluegen
            cluegen → game-core
```

## Naming map

| Concept | Protocol / type (`game-core`) | Implementation |
|---------|------------------------------|----------------|
| Clue ranking | `ClueAlgorithm.rank_clues` | `CluegenClueAlgorithm`, `ScriptedClueAlgorithm` |
| Guessing | `GuessAlgorithm.guess_word` | `EmbeddingGuessAlgorithm`, `RandomGuessAlgorithm`, `ScriptedGuessAlgorithm` |
| Spymaster loop | `SpymasterPlayer` | `CNOSpymasterBot` |
| Operative loop | `OperativePlayer` | `CNOOperativeBot` |
| Legacy engines | — | `cluegen.spymaster.Spymaster`, `cluegen.operative.Operative` (internal; rename later) |

## Intentional duplication

- **`TeamColor` / `Role`** exist in both `cno-sdk` (wire) and `game-core` (domain). `cno-bots.views` bridges them with casts so `cno-sdk` stays free of `game-core`.
- **Interactive clue picking** lives only in `apps/cno` (`prompt_select_clue`) and is injected into `CNOSpymasterBot` via `select_clue`, not in `cno-bots`.

## Items to revisit later

- **`Game` protocol** for non-CNO backends: extract connect/wait/submit from `CNOSpymasterBot` when a second backend exists.
- **Rename** internal `Spymaster` / `Operative` classes in `cluegen` to e.g. `ClueEngine` / `GuessEngine` to avoid confusion with `SpymasterPlayer`.
- **`browser_game`** could move behind a separate “orchestration” module if more match modes appear.
- **Orphan cleanup**: ensure no stale `packages/cno` copy remains in forks/branches.

## Static checking

- **Ruff** with `UP` (pyupgrade) for Python 3.12 syntax.
- **Mypy** `strict` on `game_core`, `cno_sdk`, `cluegen`, `cno_bots`, `cno`; protocols use `@runtime_checkable` for `isinstance` checks in tests.
