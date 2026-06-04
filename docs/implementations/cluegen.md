# cluegen

**Path:** [`packages/cluegen`](https://github.com/cmlees0617/codenames-ai/tree/main/packages/cluegen)

## Public API

### Algorithms (implement `game-core` protocols)

| Class | Protocol |
|-------|----------|
| `CluegenClueAlgorithm` | `ClueAlgorithm` |
| `EmbeddingGuessAlgorithm` | `GuessAlgorithm` |
| `RandomGuessAlgorithm` | `GuessAlgorithm` |
| `ScriptedClueAlgorithm` / `ScriptedGuessAlgorithm` | Tests |

### Internal engines (not player protocols)

| Class | Module | Role |
|-------|--------|------|
| `ClueEngine` | `cluegen.clue_engine` | Vocab + embeddings; `generate_clue`, `generate_ranked_clues` |
| `GuessEngine` | `cluegen.guess_engine` | ABC for batch `guess(clue, count)` |
| `EmbeddingGuessEngine` | `cluegen.guess_engine` | Cosine similarity guesses |
| `LLMGuessEngine` | `cluegen.guess_engine` | Local HF model guesses |

Rename note: `ClueEngine` / `GuessEngine` replace the old names `Spymaster` / `Operative` to avoid confusion with [`SpymasterPlayer`](../interfaces/spymaster-player.md).

## Data

Vocabulary files under `packages/cluegen/data/`.

## Demo

```bash
uv run python -m cluegen
```
