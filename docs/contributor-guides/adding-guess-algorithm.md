# Add a guess algorithm

## Problem

Operative bots must choose one guess (or pass) per call using only information visible to operatives — no hidden card colors.

## When to use

- New similarity metric, LLM reasoning, or rule-based guessing
- Scripted bots for integration tests

## Contract

Implement [`GuessAlgorithm`](../interfaces/guess-algorithm.md):

```python
def guess_word(self, state: OperativeView) -> GuessAction:
```

**Invariants:**

- Read `state.current_clue`, `state.guesses_remaining`, and unrevealed words on `state.board`
- Do not assume access to hidden colors on unrevealed tiles
- Return `GuessAction.guess(word)` or `GuessAction.end_turn()`

`CNOOperativeBot` calls this in a loop until the server ends the operative phase.

## Steps

### 1. Implement the protocol

```python
from game_core.types import GuessAction
from game_core.views import OperativeView

class MyGuessAlgorithm:
    def guess_word(self, state: OperativeView) -> GuessAction:
        if state.guesses_remaining <= 0:
            return GuessAction.end_turn()
        ...
```

Stateful algorithms (e.g. queue of guesses per clue) may store state on `self`; reset when `current_clue` changes (see `EmbeddingGuessAlgorithm`).

### 2. Wire into `build_player`

Edit `cno_bots.factory._build_operative` or pass your instance when constructing `CNOOperativeBot` in tests.

### 3. Test offline

Build an `OperativeView` with `BoardTileView` rows (no color on unrevealed cards). Assert protocol with `isinstance(algo, GuessAlgorithm)` in tests.

## Example: scripted queue

Use [`ScriptedGuessAlgorithm`](../implementations/cluegen.md) for live integration tests — queue words at init from host `GameState` in `run_full_game`.

## Related

- [GuessAlgorithm interface](../interfaces/guess-algorithm.md)
- [Types & views](../interfaces/types-and-views.md)
