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
| `static_embedding` | `StaticEmbeddingGuessAlgorithm` | Embed clue in full GloVe; top-K board words by cosine |
| `softmax_embedding` | `SoftmaxEmbeddingGuessAlgorithm` | Embed clue in full GloVe; sample K board words from softmax |
| `llm` | `LlmGuessAlgorithm` | Local instruct LLM; JSON schema `{"words": [...]}` |
| `cluegen_embedding` | `StaticCluegenEmbeddingGuessAlgorithm` | ``all-MiniLM-L6-v2`` for clue + board (cluegen sanity check; optional) |

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

### Full-game spymaster simulation (5000 boards)

The default benchmark runs **all three** operative test conditions: 3 × 5000 = **15,000**
games per spymaster, with one JSON file per operative:

``data/results/{spymaster_name}_{operative_kind}.json``

(e.g. ``my-model_static_embedding.json``, ``my-model_softmax_embedding.json``,
``my-model_llm.json``). Each file records both ``spymaster_name`` and ``operative_kind``.

Use :func:`~clue_eval.simulation.run_spymaster_benchmark_all_operatives` or the CLI example
below. For a single operative, use :class:`~clue_eval.simulation.SpymasterSimulationRunner`
with one ``operative_kind``.

Game loop (test spymaster on whichever team has **more** words on that board, plus
the matching operative):

1. Spymaster ranks clues; illegal clue (including empty / no clue) → **abort** (only use of abort).
2. Operative makes at most ``count`` guesses (no ``count + 1`` bonus). Wrong guess or
   pass ends the turn. Assassin → **loss**; all team words → **win**.
3. Opponent reveals one unrevealed word on their team (perfect guess, one per round).
4. **Loss** if the assassin is hit or all opponent words are revealed (8 opponent turns on a
   standard 8-red layout when reds are only removed in step 3).
5. Each game in the results JSON includes ``difficulty_*`` fields when boards carry
   ``difficulty`` metadata for correlation with win/loss/abort.

Expose ``name`` on your spymaster (see :class:`~game_core.algorithms.IdentifiableClueAlgorithm`)
for result filenames, or the class name is used.

```python
from clue_eval.simulation import run_spymaster_benchmark_all_operatives

run_spymaster_benchmark_all_operatives(MySpymaster())
```

CLI (all three operatives by default):

``uv run python packages/clue-eval/examples/run_spymaster_simulation.py --spymaster-module mypkg:MySpymaster``

Example [`cluegen`](cluegen.md) spymaster: ``--cluegen`` (same as
``--spymaster-module cluegen.algorithms.clue:CluegenClueAlgorithm``). Progress: one
tqdm bar per operative condition (5000 games each) plus an outer bar over the three conditions.

Debug run (first 50 boards, one operative, separate results file)::

``uv run python packages/clue-eval/examples/run_spymaster_simulation.py --cluegen --operative static_embedding --sample 50``

Writes ``cluegen_static_embedding_sample50.json`` (sample runs never overwrite full-benchmark files).

Flags:

- ``--operative KIND`` — ``static_embedding``, ``softmax_embedding``, or ``llm`` (default: all three)
- ``-n`` / ``--sample`` / ``--limit`` — first N boards only

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

The Codenames word list (`data/words.txt`, 400 words) has precomputed **glove-wiki-gigaword-300** vectors in `data/glove-wiki-gigaword-300.npz` (300 dimensions). Board difficulty scoring and embedding operatives compare against this packaged matrix.

**Clue encoding** for static/softmax operatives uses the **full** `glove-wiki-gigaword-300` model (lazy-loaded via gensim on first use), so arbitrary English clue words like `MARGINS` are embedded and compared to the 400 board-word vectors. GloVe is a strong static baseline for word similarity; it is not contextual like sentence-transformers.

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
