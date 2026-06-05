# clue-eval

**Path:** `packages/clue-eval`

## Purpose

**Predefined clue tests** and a **model-agnostic harness** for running any [`ClueAlgorithm`](../interfaces/clue-algorithm.md) through them.

Contributors implement `ClueAlgorithm`, then run the repo catalog—they are **not** scored against another algorithm in the monorepo (including `cluegen`).

Depends on **`game-core` only**.

## Layout

```text
packages/clue-eval/
  data/                    # test_boards.json, words.txt, glove-wiki-gigaword-300.npz
  src/clue_eval/
    boards/                # layouts, factory, SpymasterView conversion
    scenarios/             # Scenario + ScenarioRunner
    suite/                 # ClueTest, TestSuite, catalog, SuiteRunner
    benchmark/             # timing / summary printing
    operatives/            # three standard operative test conditions
    clues/                 # spymaster clue legality (stem, homophone, …)
    demos/                 # StubClueAlgorithm for CI smoke
  tests/
```

## Predefined catalog

| Type | Role |
|------|------|
| `ClueTest` | One catalog entry (`id`, `Scenario`, description, tags) |
| `TestSuite` | Named list of tests |
| `default_suite()` | Shipped starter catalog (fixture boards today; more cases TBD) |

Add cases in `clue_eval.suite.catalog` (or JSON loaders) as requirements grow—legality checks, assassin safety, etc. can hang off `ClueTest` later.

## Usage

```python
from clue_eval import SuiteRunner, default_suite
from my_package import MyClueAlgorithm

results = SuiteRunner(MyClueAlgorithm()).run_suite(default_suite())
```

### Operative test conditions

Evaluate a spymaster clue against a fixed operative agent (same GloVe space as board scoring):

| Kind | Class | Behavior |
|------|--------|----------|
| `static_embedding` | `StaticEmbeddingGuessAlgorithm` | Top-K board words by cosine to clue |
| `softmax_embedding` | `SoftmaxEmbeddingGuessAlgorithm` | Sample K words from softmax over top candidates |
| `llm` | `LlmGuessAlgorithm` | Local instruct LLM; JSON schema `{"words": [...]}` |

```python
from clue_eval import ScenarioRunner
from clue_eval.operatives import create_operative_algorithm

runner = ScenarioRunner(
    MyClueAlgorithm(),
    operative_condition="static_embedding",
)
# or: guess_algorithm=create_operative_algorithm("softmax_embedding", softmax_seed=42)
```

Install `llm` optional deps for the LLM operative: `uv sync --package clue-eval --extra llm`.

### Clue legality

`validate_clue_legality(clue_word, count, visible_board_words)` enforces:

1. Exactly one non-empty clue token (no spaces).
2. No substring / shared Snowball stem / WordNet lemma with any visible board word.
3. No Double Metaphone homophone overlap with a visible board word.
4. Count ≥ 1.

`ScenarioRunner` adds a `clue_legality` block for the top-ranked clue.

Smoke run (stub algorithm, no ML):

```bash
uv run python -m clue_eval --stub
```

## Scenario fields (model-agnostic)

| Field | Meaning |
|-------|---------|
| `board` | Tile layout (`blues` / `reds` / … are colors on the board) |
| `team` | Spymaster's team |
| `clue_limit` | `rank_clues(..., limit=...)` |
| `expected_targets` | Optional pass/fail on top clue's `intended_targets` |

Algorithm-specific options (e.g. vocabulary pruning) live on **your** implementation, not on `Scenario`.

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
uv run python packages/clue-eval/examples/generate_standard_board_set.py
```

Writes ``packages/clue-eval/data/standard_boards_5000.json`` (``beta=2.0``, ``seed=42`` by default).
Load with ``load_boards_from_json`` and split into train/test in application code.

## Word embeddings (GloVe)

The Codenames word list (`data/words.txt`, 400 words) has precomputed **glove-wiki-gigaword-300** vectors in `data/glove-wiki-gigaword-300.npz` (300 dimensions). GloVe is a strong static baseline for word similarity; it is not contextual like sentence-transformers.

Regenerate after changing `words.txt`:

```bash
uv sync --package clue-eval --extra embeddings
uv run --extra embeddings clue-eval-embed
# or: uv run --extra embeddings python -m clue_eval.embeddings
```

Load in code:

```python
from clue_eval.embeddings import EmbeddingStore

store = EmbeddingStore.load()
vec = store.vector_for("APPLE")
```

## Optional example package

[`cluegen`](cluegen.md) ships an embedding-based `ClueAlgorithm` you can study or use in live bots. Evaluating it means running the **same** `default_suite()` with `CluegenClueAlgorithm()`—not a separate benchmark path.
