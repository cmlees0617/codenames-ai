# codenames-ai

Python monorepo for [Codenames Online](https://codenames.game) bots: wire client, CLI, and offline clue generation.

**Documentation:** https://cmlees0617.github.io/codenames-ai/

```bash
uv sync --all-packages --group dev
uv run cno                          # join a live room
uv run python -m cluegen             # optional embedding example
uv run python packages/clue-eval/examples/generate_standard_board_set.py  # benchmark boards
```

On branch `feature/spymaster-test-pipeline` only:

```bash
uv run python -m clue_eval --stub    # catalog smoke test
uv run python packages/clue-eval/examples/run_spymaster_simulation.py --cluegen --sample 10
```

The spymaster test pipeline is **work in progress** and likely to be massively reworked—see [clue-eval docs](docs/implementations/clue-eval.md).
