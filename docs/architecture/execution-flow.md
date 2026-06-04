# Execution flow

How a single `uv run cno <room> red-spymaster` invocation runs through the layers.

## CLI startup

```mermaid
sequenceDiagram
  participant User
  participant CLI as apps/cno
  participant Factory as cno_bots.factory
  participant Runner as cno_bots.runner

  User->>CLI: argv or interactive prompts
  CLI->>CLI: parse_role, validate room
  CLI->>Factory: PlayerBuildOptions + select_clue?
  Factory->>Factory: build_player → CNOSpymasterBot
  CLI->>Runner: run_player(bot)
  Runner->>Runner: install SIGINT handler
```

**Invariant:** CLI never calls `CNOClient` directly.

## Spymaster turn (one iteration)

```mermaid
sequenceDiagram
  participant Bot as CNOSpymasterBot
  participant Client as CNOClient
  participant Algo as ClueAlgorithm
  participant Views as cno_bots.views

  Bot->>Client: wait_for_spymaster_turn
  Client-->>Bot: GameState
  Bot->>Views: to_spymaster_view
  Views-->>Bot: SpymasterView
  Bot->>Algo: rank_clues(view) [thread pool]
  Algo-->>Bot: list Clue
  Bot->>Bot: select_clue (auto or CLI)
  Bot->>Client: give_clue(word, targets)
```

**Invariant:** `ClueAlgorithm` is synchronous and receives only `SpymasterView` (full hidden colors).

## Operative turn (one guess)

```mermaid
sequenceDiagram
  participant Bot as CNOOperativeBot
  participant Client as CNOClient
  participant Algo as GuessAlgorithm
  participant Views as cno_bots.views

  Bot->>Client: wait_for_operative_turn
  loop While guess_limit > 0
    Bot->>Views: to_operative_view
    Bot->>Algo: guess_word(view)
    Algo-->>Bot: GuessAction
    alt pass_turn
      Bot->>Client: end_guessing
    else word
      Bot->>Client: guess_card(word)
    end
  end
```

**Invariant:** `OperativeView` omits unrevealed card colors; algorithms must not rely on hidden bucket information.

## Full four-bot match

`cno_bots.game.run_full_game` creates a room, seats four clients, starts the match, and runs four `play()` tasks with `Scripted*` algorithms in integration tests. Production CLI typically runs **one** bot per process.

See [CLI reference](../cli/reference.md) and [cno-bots implementation](../implementations/cno-bots.md).
