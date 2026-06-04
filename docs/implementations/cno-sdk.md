# cno-sdk

**Path:** [`packages/cno-sdk`](https://github.com/cmlees0617/codenames-ai/tree/main/packages/cno-sdk)

## Responsibility

Low-level client for [codenames.game](https://codenames.game):

- `CNOClient` — Socket.IO / boardgame.io
- `GameState`, moves, patches, room creation
- Session logging (`~/.codenames-ai/sessions.jsonl`)

## Must not

- Import `game-core` or `cluegen`

## Key types

`TeamColor`, `Role`, `BoardCard` in `cno_sdk.state` — literals aligned with [`game_core.types`](../interfaces/types-and-views.md).

**Source:** [`packages/cno-sdk/src/cno_sdk/`](https://github.com/cmlees0617/codenames-ai/tree/main/packages/cno-sdk/src/cno_sdk)
