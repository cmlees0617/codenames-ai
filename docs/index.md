# codenames-ai contributor documentation

This site documents the **codenames-ai** Python monorepo for **contributors and maintainers**. It is not end-user product documentation for codenames.game players.

## What this repository does

The project connects AI bots to [Codenames Online](https://codenames.game): spymasters rank clues from board state, operatives guess words, and a thin CLI starts bots in live rooms. Offline embedding search lives in **cluegen**. **clue-eval** provides stratified benchmark boards and GloVe-based difficulty scoring.

## How to read this site

| Section | Use when you need to… |
|---------|------------------------|
| [Getting started](getting-started.md) | Set up the workspace and run bots locally |
| [Architecture](architecture/overview.md) | Understand packages, dependencies, and runtime flow |
| [Interfaces](interfaces/clue-algorithm.md) | Implement or call extension points (`Protocol`s) |
| [Contributor guides](contributor-guides/index.md) | Add algorithms, backends, or CLI behavior |
| [CLI reference](cli/reference.md) | Run and configure the `cno` command |
| [API reference (selected)](api/index.md) | Generated signatures for key protocols (supplement only) |
| [ADRs](adrs/index.md) | Read why major design choices were made |

## Documentation principles

This site is for **contributors and maintainers**, not external end users.

**Prioritize:**

- Architecture and package relationships
- Interface contracts and extension points
- Contributor workflows and implementation guides
- CLI behavior and execution flow
- Design intent (ADRs)

**Generated API docs** ([API reference](api/index.md)) supplement narrative docs; they do not replace them.

**When adding functionality:**

1. Document new extension points and update [interfaces](interfaces/clue-algorithm.md) if contracts change.
2. Update [architecture](architecture/overview.md) diagrams when boundaries shift.
3. Add or update [contributor guides](contributor-guides/index.md) when workflows change.
4. Include usage examples and explain *why*, not only *how*.
5. Avoid exhaustive mkdocstrings for internal ML helpers unless they help contributors.

**Good questions to answer:** What problem does this solve? When should I use it? How do I extend it? What invariants must hold?

## Repository layout

```text
apps/cno/              CLI entrypoint (argparse, questionary)
packages/cno-bots/     CNO player bots + orchestration
packages/cno-sdk/      codenames.game wire client
packages/clue-eval/    Benchmark board generation + GloVe difficulty scoring
packages/cluegen/      Optional example embedding algorithms
packages/game-core/    Domain types and protocols
```

See [Architecture overview](architecture/overview.md) for the dependency diagram.
