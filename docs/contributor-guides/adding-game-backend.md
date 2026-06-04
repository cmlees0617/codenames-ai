# Add a game backend

## Problem

Today only codenames.game is supported. `GameBackend` defines the async transport contract so spymaster/operative **players** can eventually work with tabletop apps, local simulators, or other sites — without duplicating turn loops.

## Current status

- [`GameBackend`](../interfaces/game-backend.md) is defined in `game_core.backends`
- **No implementation exists**
- `CNOSpymasterBot` / `CNOOperativeBot` call `CNOClient` directly

## When to implement

You have a second Codenames platform and want to reuse `ClueAlgorithm`, `GuessAlgorithm`, and player protocols.

## Recommended approach

### 1. Implement `GameBackend` in a new package or `cno-bots`

| Method | Maps to today (CNO) |
|--------|---------------------|
| `connect` | `CNOClient.connect` |
| `join` | `join_team` |
| `wait_for_spymaster_turn` | `wait_for_spymaster_turn` + `to_spymaster_view` |
| `wait_for_operative_turn` | `wait_for_operative_turn` + `to_operative_view` |
| `submit_clue` | `give_clue` |
| `submit_guess` | `guess_card` / `end_guessing` |
| `disconnect` | `leave` |

Keep view mapping next to the backend (like `cno_bots.views` for CNO).

### 2. Refactor players to accept `GameBackend`

Replace direct `CNOClient` fields with a backend protocol instance. CNO would provide `CNOGameBackend` wrapping the client.

**Do not** merge spymaster and operative into one player type.

### 3. Document and ADR

Add an ADR describing the backend, auth, and state mapping. Update [architecture overview](../architecture/overview.md) diagram.

## Constraints

- Backends return **domain views**, not wire `GameState`
- Algorithms stay unchanged if views are faithful
- CLI stays thin — only selects backend via config if multiple exist

## Related

- [GameBackend interface](../interfaces/game-backend.md)
- [ADR-0001 Layered monorepo](../adrs/0001-layered-monorepo.md)
