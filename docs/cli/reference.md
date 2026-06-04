# CLI reference

The `cno` command is the operator entrypoint for joining a [codenames.game](https://codenames.game) room as one bot.

**Implementation:** `apps/cno` — see [CLI implementation](../implementations/cno-cli.md).

## Usage

```bash
uv run cno [room] [role] [options]
```

With no arguments, the CLI runs **interactive mode** (questionary prompts).

## Positional arguments

| Argument | Description |
|----------|-------------|
| `room` | Room slug from the URL (e.g. `halok-jonah`) |
| `role` | `red-spymaster`, `blue-spymaster`, `red-operative`, `blue-operative` |

**Shorthand:** `uv run cno red-spymaster` sets role only; you will still be prompted for a room.

## Options

| Flag | Roles | Effect |
|------|-------|--------|
| `--nickname NAME` | All | Display name in room (default: `RedSpymasterBot`, etc.) |
| `--interactive` | Spymaster | Pick one clue from top-ranked options (questionary) |
| `--random-operative` | Operative | Use random unrevealed tiles instead of embeddings |

## Default algorithms

| Role | Default | Flag override |
|------|---------|-----------------|
| Spymaster | `CluegenClueAlgorithm` | — |
| Spymaster (selection) | Auto-pick best clue | `--interactive` |
| Operative | `EmbeddingGuessAlgorithm` | `--random-operative` |

## Execution flow

1. Parse or prompt for configuration
2. `cno_bots.factory.build_player(PlayerBuildOptions(...))`
3. `cno_bots.runner.run_player` until game over or Ctrl+C
4. Graceful leave via `ShutdownController`

See [Execution flow](../architecture/execution-flow.md).

## Examples

```bash
uv run cno halok-jonah red-spymaster
uv run cno halok-jonah blue-operative --nickname MyBot
uv run cno halok-jonah red-spymaster --interactive
uv run cno
```

## Logging

The CLI configures Python logging at **DEBUG** for all runs.

## Session persistence

Disconnected sessions may be logged under `~/.codenames-ai/sessions.jsonl` via `cno-sdk` (see [cno-sdk](../implementations/cno-sdk.md)).
