# ADR-0002: Thin CLI and cno-bots package

**Status:** Accepted

## Context

The CLI needs questionary for interactive mode and argparse for scripting, but game loops and `CNOClient` usage should stay testable without terminal UI. Human clue selection is a presentation concern, not core bot logic.

## Decision

- Move all player bots, `build_player`, `run_full_game`, and `GameState` view mapping to **`packages/cno-bots`**
- Limit **`apps/cno`** to parsing, prompts, and calling `build_player` + `run_player`
- Inject human clue picking via `select_clue: Callable[[list[Clue]], Clue | None]` on `CNOSpymasterBot`, implemented in the CLI as `prompt_select_clue`

## Consequences

**Positive**

- `cno-bots` has no dependency on questionary
- Same bots usable from tests, orchestration, or other entrypoints
- Clear contributor rule: UI in CLI, behavior in bots/algorithms

**Negative**

- Two packages to touch for a new end-to-end feature (CLI flag + factory wiring)

**Follow-ups**

- Optional config file for algorithm selection without new CLI code paths
