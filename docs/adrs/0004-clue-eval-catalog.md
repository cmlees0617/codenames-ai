# ADR-0004: clue-eval board benchmark; cluegen as optional example

**Status:** Accepted (amended)

## Context

Spymaster research needs **reproducible board sets** with known difficulty, not ad-hoc layouts per experiment. Contributors also need an **optional** embedding example (`cluegen`) that does not become a required dependency of board tooling or the live bot stack.

On `feature/clue-eval-package`, **`clue-eval` is scoped to board generation and GloVe difficulty scoring only**. Full-game simulation, operative test conditions, and the predefined clue catalog live on the separate `feature/spymaster-simulation` branch.

## Decision

1. **`clue-eval`** owns stratified board generation (`BoardFactory`), per-team GloVe difficulty, packaged embeddings (`words.txt` → `glove-wiki-gigaword-300.npz`), and the shipped `standard_boards_5000.json` benchmark file.
2. **`cluegen`** remains an **optional example package** (embedding `ClueEngine`, `CluegenClueAlgorithm`, guess engines). It does not depend on `clue-eval`.
3. **`cno-bots`** may default to `CluegenClueAlgorithm` for convenience, but `PlayerBuildOptions` accepts injected `clue_algorithm` / `guess_algorithm`.
4. Algorithm evaluation harnesses (scenario runners, operatives, full-game simulation) are **out of scope** on this branch; use `feature/spymaster-simulation` when merging that work.

## Consequences

**Positive**

- Board benchmark is ML-light (GloVe only for difficulty labels)
- Clear split between reproducible data (`clue-eval`) and example algorithms (`cluegen`)
- Large simulation code can evolve on its own branch without blocking board PRs

**Negative**

- Contributors on this branch must not expect `SuiteRunner` / `ScenarioRunner` in `clue_eval`
- Docs and ADR title still reference “catalog” historically; behavior is board-first until simulation merges

**Follow-ups**

- Merge `feature/spymaster-simulation` when the full-game benchmark is ready
- Expand board metadata or generation strategies as research needs grow
