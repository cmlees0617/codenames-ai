# ADR-0004: Predefined clue-eval catalog; cluegen as optional example

**Status:** Accepted

## Context

Contributors should validate custom `ClueAlgorithm` implementations against a **shared, predefined test catalog** maintained in the repo—not against whichever embedding model ships in `cluegen`. The embedding spymaster is one possible implementation, useful for demos and as a reference for authors, but it must not be a required dependency of evaluation or of the core bot stack.

## Decision

1. **`clue-eval`** owns the predefined test catalog (`ClueTest`, `TestSuite`, `suite/catalog.py`) and runs any `ClueAlgorithm` through `SuiteRunner` / `ScenarioRunner`.
2. **`cluegen`** remains an **optional example package** (embedding `ClueEngine`, `CluegenClueAlgorithm`, guess engines). It does not depend on `clue-eval` and is not invoked by the eval harness.
3. **`cno-bots`** may default to `CluegenClueAlgorithm` for convenience, but `PlayerBuildOptions` accepts injected `clue_algorithm` / `guess_algorithm` so live play does not require the example package conceptually.
4. New tests are added to `clue_eval.suite.catalog` (or JSON under `clue-eval/data/`) over time; comparing two contributor algorithms means running the **same suite** twice, not comparing to `cluegen`.

## Consequences

**Positive**

- Clear product goal: pass the catalog, not beat the maintainer's model
- Eval harness stays ML-free and fast in CI
- Example code can evolve or be forked without breaking tests

**Negative**

- `cno-bots` still lists `cluegen` as a dependency for default CLI behavior (practical, not architectural)
- Catalog is minimal until more cases are authored

**Follow-ups**

- Expand `ClueTest` with assertions beyond `expected_targets` (legality, safety, etc.)
- Optional JSON-driven catalog files per suite
