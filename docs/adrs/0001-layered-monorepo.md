# ADR-0001: Layered monorepo with game-core protocols

**Status:** Accepted

## Context

Contributors need to swap clue and guess strategies, test logic without live servers, and optionally support non-CNO backends later. A single package mixing Socket.IO, ML, and argparse becomes hard to test and creates import cycles.

## Decision

Split the repository into layers:

1. **game-core** — domain views and `Protocol` extension points
2. **cluegen** — algorithm implementations (and internal ML engines)
3. **cno-sdk** — codenames.game wire client only
4. **cno-bots** — CNO-specific player loops and view adapter
5. **apps/cno** — CLI only

Algorithms depend on `game-core`; `cno-sdk` does not depend on `game-core`.

## Consequences

**Positive**

- Unit tests for algorithms use plain dataclasses
- Clear “where does this code belong?” rules
- Future `GameBackend` can sit between players and transport

**Negative**

- `TeamColor` / `Role` duplicated at the SDK boundary (see ADR-0003)
- More packages to navigate

**Follow-ups**

- Implement `GameBackend` for CNO and refactor bots off raw `CNOClient`
