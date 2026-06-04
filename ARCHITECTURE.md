# Architecture and layer boundaries

Full interface and implementation docs: **[docs/README.md](docs/README.md)**.

## Package layers

| Layer | Package | Responsibility | Must not |
|-------|---------|----------------|----------|
| Wire | `cno-sdk` | Socket.IO, BGIO state parsing, moves | Import `game-core` or `cluegen` |
| Domain | `game-core` | Role views, types, protocols | Import `cno-sdk`, do I/O, or load ML models |
| Algorithms | `cluegen` | `ClueAlgorithm` / `GuessAlgorithm` + internal engines | Import `cno-sdk` or know about rooms/clients |
| CNO players | `cno-bots` | View adapter, player bots, orchestration | Import `questionary` or parse CLI strings |
| CLI | `apps/cno` | Args + interactive UI → `cno_bots` | Game loops or clue/guess logic |

```text
apps/cno (CLI)
    → cno-bots (CNO adapter + bots)
        → cno-sdk, game-core, cluegen
            cluegen → game-core
```

## Naming map

| Concept | Protocol (`game-core`) | Implementation |
|---------|------------------------|----------------|
| Clue ranking | `ClueAlgorithm` | `CluegenClueAlgorithm`, `ScriptedClueAlgorithm` |
| Guessing | `GuessAlgorithm` | `EmbeddingGuessAlgorithm`, `RandomGuessAlgorithm`, `ScriptedGuessAlgorithm` |
| Spymaster loop | `SpymasterPlayer` | `CNOSpymasterBot` |
| Operative loop | `OperativePlayer` | `CNOOperativeBot` |
| ML clue search | — | `cluegen.ClueEngine` |
| ML batch guess | — | `cluegen.GuessEngine` / `EmbeddingGuessEngine` |
| Room transport (future) | `GameBackend` | Not implemented; CNO uses `CNOClient` directly |

## Intentional duplication

- **`TeamColor` / `Role`** in `cno-sdk` and `game-core` — same literals, separate types for dependency isolation. Documented in [`docs/interfaces/types-and-views.md`](docs/interfaces/types-and-views.md). `cno_bots.views` is the adapter.
- **Interactive clue picking** — only in `apps/cno` (`prompt_select_clue`), passed as `select_clue` into `CNOSpymasterBot`.

## Static checking

- **Ruff** with `UP` (Python 3.12) on `apps` + `packages`.
- **Mypy** strict on `game_core`, `cno_bots`, `cno`, `cluegen.algorithms`.
- Legacy `cluegen` engines (`clue_engine.py`, `guess_engine.py`) excluded from mypy until typed.

## Possible follow-ups

- Implement `GameBackend` for CNO and refactor bots off raw `CNOClient`.
- Type-check `cno-sdk` and legacy cluegen engines.
- Split `browser_game` / `game` into a dedicated orchestration module if more match modes appear.
