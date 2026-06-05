# ADR-0004: clue-eval boards, catalog, and spymaster test pipeline

**Status:** Accepted (amended)

## Context

Spymaster research needs **reproducible board sets** with known difficulty, not ad-hoc layouts per experiment. Contributors also need an **optional** embedding example (`cluegen`) that does not become a required dependency of board tooling or the live bot stack.

**Merged to `main` (PR #13):** stratified board generation (`BoardFactory`), per-team GloVe difficulty, packaged embeddings, and `standard_boards_5000.json`.

**On `feature/spymaster-test-pipeline` (not yet on `main`):** a predefined clue-test catalog (`SuiteRunner` / `ScenarioRunner`) and an **in-progress full-game spymaster test pipeline** (fixed operative agents, simulated games, result JSON). That pipeline is **experimental**—game rules, operative kinds, and output formats are likely to be massively reworked before merge.

## Decision

1. **`clue-eval`** owns board generation and difficulty scoring (stable), plus—on the test-pipeline branch—the catalog and WIP simulation harness.
2. **`cluegen`** remains an **optional example package**. It does not depend on `clue-eval`.
3. **`cno-bots`** may default to `CluegenClueAlgorithm` for convenience, but `PlayerBuildOptions` accepts injected `clue_algorithm` / `guess_algorithm`.
4. Contributors validate custom `ClueAlgorithm` implementations against the **shared catalog** and (optionally) the WIP full-game benchmark—not against `cluegen` as a required baseline.

## Consequences

**Positive**

- Stable, ML-light board data (GloVe only for difficulty labels) ships independently of the experimental pipeline
- Clear split between reproducible data (`clue-eval` boards), catalog tests, and example algorithms (`cluegen`)
- Pipeline can evolve on its branch without blocking board PRs

**Negative**

- `main` and `feature/spymaster-test-pipeline` temporarily describe different `clue-eval` scopes until the pipeline merges
- Catalog is minimal until more cases are authored
- Pipeline APIs are unstable; docs must carry WIP caveats

**Follow-ups**

- Merge and stabilize the spymaster test pipeline after design review
- Expand `ClueTest` with assertions beyond `expected_targets` (legality, safety, etc.)
- Optional JSON-driven catalog files per suite
