# clue-eval

**Path:** `packages/clue-eval`

## Purpose

**Board generation and difficulty scoring** for Codenames spymaster benchmarks.

Provides GloVe-based per-team difficulty, stratified board factories, and the packaged
``standard_boards_5000.json`` set.

## Layout

```text
packages/clue-eval/
  data/                    # words.txt, glove-wiki-gigaword-300.npz, standard_boards_5000.json
  examples/
    generate_standard_board_set.py
  src/clue_eval/
    boards/                # layouts, factory, difficulty, I/O
    embeddings/            # GloVe store and generation CLI
  tests/
```

## Board difficulty and stratified generation

Per-team difficulty (GloVe cosine similarity, default ``beta=2.0``):

```text
cohesion  = log_mean_sim(targets, targets)
confusion = log_mean_sim(targets, others) + beta * log_max_sim(targets, assassin)
difficulty = confusion / (confusion + cohesion)   # in [0, 1], higher = harder

``log_sim(c) = log(1 + c) / log(2)`` for each non-negative cosine; negative pairs are
omitted from means. Boards where a team has no non-negative target–target pairs are skipped.
```

Easy boards score near **0** (high cohesion, low confusion). Hard boards score near
**1** (low cohesion, high confusion with other cards or the assassin).

- **Blue** targets = ``blues``; others = ``reds`` + ``civilians`` + ``assassins``
- **Red** targets = ``reds``; others = ``blues`` + ``civilians`` + ``assassins``

``FixtureBoard`` may include ``difficulty: {"blue": float, "red": float}``.

Generate ``n`` boards with evenly spaced mean difficulty:

```python
from clue_eval.embeddings import EmbeddingStore
from clue_eval.boards import BoardFactory
from clue_eval.paths import default_standard_boards_path

store = EmbeddingStore.load()
path = BoardFactory.generate_and_save_uniform_difficulty_boards(
    10, store, default_standard_boards_path().with_name("my_boards.json"), seed=0
)
```

Saved JSON is ordered **easiest → hardest** (``id`` 1 = easiest).

### Standard 5000-board benchmark set

From the repository root:

```bash
uv sync --package clue-eval --extra embeddings
uv run python packages/clue-eval/examples/generate_standard_board_set.py
```

Writes ``packages/clue-eval/data/standard_boards_5000.json`` (``beta=2.0``, ``seed=42`` by default).
Load with ``load_boards_from_json`` and split into train/test in application code.

## Word embeddings (GloVe)

The Codenames word list (`data/words.txt`, 400 words) has precomputed **glove-wiki-gigaword-300** vectors in `data/glove-wiki-gigaword-300.npz` (300 dimensions).

Regenerate after changing `words.txt`:

```bash
uv sync --package clue-eval --extra embeddings
uv run --extra embeddings clue-eval-embed
```

Load in code:

```python
from clue_eval.embeddings import EmbeddingStore

store = EmbeddingStore.load()
vec = store.vector_for("APPLE")
```
