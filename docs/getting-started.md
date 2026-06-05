# Getting started

For contributors working on the monorepo.

## Requirements

- Python **3.12+**
- [uv](https://docs.astral.sh/uv/)

## Install

```bash
git clone <repo-url>
cd codenames-ai
uv sync --all-packages --group dev
```

This installs workspace packages (`game-core`, `clue-eval`, `cluegen`, `cno-sdk`, `cno-bots`, `cno`) and dev tools (pytest, ruff, mypy, MkDocs).

## Run predefined clue tests

```bash
# Catalog smoke test (stub ClueAlgorithm, no ML)
uv run python -m clue_eval --stub
```

Plug in your own `ClueAlgorithm` via `SuiteRunner` (see [clue-eval](implementations/clue-eval.md)).

Optional embedding example (not the catalog):

```bash
uv run python -m cluegen
```

## Spymaster test pipeline (experimental)

On branch `feature/spymaster-test-pipeline`, `clue-eval` includes a **work-in-progress** full-game benchmark: spymasters are scored against fixed operative agents on the standard 5000-board set.

!!! warning "Likely to be reworked"
    Operative conditions, game rules, CLI flags, and result JSON are unstable. Expect breaking changes without notice while the pipeline is designed.

```bash
uv sync --package clue-eval --extra embeddings --extra llm
uv run python packages/clue-eval/examples/run_spymaster_simulation.py --cluegen --sample 10
```

Debug flags: `--operative KIND`, `-n` / `--sample`. Full details: [clue-eval](implementations/clue-eval.md#spymaster-test-pipeline-full-game-benchmark-5000-boards).

## Run the CLI

```bash
# Interactive prompts
uv run cno

# Direct invocation
uv run cno <room-slug> red-spymaster
uv run cno <room-slug> red-spymaster --interactive
uv run cno <room-slug> blue-operative --random-operative
```

## Run checks

```bash
uv run pytest -m "not integration"
uv run ruff check apps packages
uv run mypy -p game_core -p cno_bots -p cno -p cluegen.algorithms
```

Live integration tests (network + codenames.game):

```bash
uv run pytest -m integration
```

## Build documentation locally

```bash
uv run mkdocs serve
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). Production builds deploy to GitHub Pages via CI (see `.github/workflows/docs.yml`).

## Where to change code

| Goal | Start here |
|------|------------|
| New clue strategy | [Add a clue algorithm](contributor-guides/adding-clue-algorithm.md) |
| Spymaster benchmark / catalog | [clue-eval](implementations/clue-eval.md) (pipeline WIP) |
| New guess strategy | [Add a guess algorithm](contributor-guides/adding-guess-algorithm.md) |
| New Codenames backend | [Add a game backend](contributor-guides/adding-game-backend.md) |
| CLI flags or prompts | [Extend the CLI](contributor-guides/extending-cli.md) |
| Wire protocol / parsing | `packages/cno-sdk` (keep free of `game-core`) |
