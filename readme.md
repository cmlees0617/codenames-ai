# codenames-ai

Python tools for playing [Codenames Online](https://codenames.game): a protocol SDK, a CLI bot, and an offline clue engine.

## Packages

| Package | Description |
|---------|-------------|
| `cno-sdk` | Low-level Socket.IO / boardgame.io client for codenames.game |
| `cno` | CLI and high-level bot sessions (`cno` command) |
| `cluegen` | Offline clue generation using semantic embeddings |

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)

## Setup

```bash
git clone <repo-url>
cd codenames-ai
uv sync --all-packages --group dev
```

## Quickstart

Run the interactive CLI (no arguments) — pick a role, enter a room slug, and optionally customize your nickname:

```bash
uv run cno
```

Or pass arguments directly:

```bash
# Join an existing room as red spymaster
uv run cno halok-jonah red-spymaster

# Blue operative with a custom nickname
uv run cno halok-jonah blue-operative --nickname MyBot
```

Roles: `red-spymaster`, `blue-spymaster`, `red-operative`, `blue-operative`.

If you omit `--nickname`, the bot uses a role-based default (e.g. `RedSpymasterBot`, `BlueOperativeBot`). Logging is always at DEBUG.

The bot joins the room, waits for its role each turn, and plays until the game ends. Spymaster bots give clues on every turn; operative bots guess random tiles.

```bash
# Full automated game (4 bots) — integration test
uv run pytest packages/cno/tests/test_live_full_game.py -m integration
```

Session tokens are logged to `~/.codenames-ai/sessions.jsonl` so disconnected players can be reconnected and removed later. Ctrl+C leaves the room cleanly.

## Tests

```bash
# Unit tests
uv run pytest -m "not integration"

# Live integration tests (network required)
uv run pytest -m integration
```
