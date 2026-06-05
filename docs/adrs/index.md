# Architecture Decision Records

ADRs capture **why** we chose a design, not only what the code does. Narrative docs and diagrams remain the primary reference; ADRs supplement them for major forks.

## Index

| ADR | Title | Status |
|-----|-------|--------|
| [0001](0001-layered-monorepo.md) | Layered monorepo with game-core protocols | Accepted |
| [0002](0002-thin-cli-and-cno-bots.md) | Thin CLI and cno-bots package | Accepted |
| [0003](0003-wire-domain-literals.md) | Duplicate TeamColor/Role in SDK and game-core | Accepted |
| [0004](0004-clue-eval-catalog.md) | clue-eval boards, catalog, and WIP test pipeline | Accepted (amended) |

## Template for new ADRs

Create `docs/adrs/NNNN-short-title.md` with:

- **Status** (Proposed | Accepted | Superseded)
- **Context** — problem and forces
- **Decision** — what we chose
- **Consequences** — positive, negative, follow-ups

Link from [Architecture overview](../architecture/overview.md) and relevant contributor guides.
