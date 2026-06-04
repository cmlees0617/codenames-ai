# API reference (selected)

Auto-generated signatures from docstrings via [mkdocstrings](https://mkdocstrings.github.io/). **Use narrative docs first** — these pages supplement [Interfaces](../interfaces/clue-algorithm.md) and [Contributor guides](../contributor-guides/index.md).

We intentionally **do not** generate docs for:

- Internal ML engines (`ClueEngine`, `GuessEngine`) unless you are hacking cluegen internals
- Every method on `CNOClient`
- Test fixtures and scripts

## Pages

| Page | Symbols |
|------|---------|
| [game_core protocols](game-core.md) | `ClueAlgorithm`, `GuessAlgorithm`, `SpymasterPlayer`, `OperativePlayer`, `GameBackend` |
| [cluegen algorithms](cluegen.md) | `CluegenClueAlgorithm`, `EmbeddingGuessAlgorithm`, … |
| [cno_bots factory](cno-bots.md) | `PlayerBuildOptions`, `build_player` |

## Editing generated content

Edit Python docstrings in source, not the generated Markdown. Rebuild with `uv run mkdocs build`.
