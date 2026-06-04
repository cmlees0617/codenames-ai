# ADR-0003: Duplicate wire and domain TeamColor / Role literals

**Status:** Accepted

## Context

`game-core` should define domain types for views and protocols. `cno-sdk` parses boardgame.io payloads and must remain usable without depending on `game-core` (avoid cycles and keep the SDK minimal for other tools).

## Decision

- Define `TeamColor` and `Role` as identical `Literal` aliases in both `game_core.types` and `cno_sdk.state`
- Document that values must stay in sync
- Map `GameState` → views in `cno_bots.views` at the adapter layer

We do **not** share a single type object across packages at runtime.

## Consequences

**Positive**

- Strict dependency direction: SDK ↛ game-core
- Mypy keeps wire and domain roles distinct (prevents accidental coupling)

**Negative**

- Contributors must update both literals if roles change
- Requires comment discipline in `cno_sdk.state`

**Alternatives considered**

- Moving all types into `game-core` and making `cno-sdk` depend on it — rejected to preserve SDK isolation
