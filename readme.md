# codenames-ai

Python monorepo for [Codenames Online](https://codenames.game) bots: wire client, CLI, and offline clue generation.

**Documentation:** https://cmlees0617.github.io/codenames-ai/

```bash
uv sync --all-packages --group dev
uv run cno                          # join a live room
uv run python -m clue_eval --stub    # predefined clue test catalog (smoke)
uv run python -m cluegen             # optional embedding example (not the catalog)
```

**Spymaster test pipeline** (branch `feature/spymaster-test-pipeline`): full-game benchmarks via `packages/clue-eval/examples/run_spymaster_simulation.py`. This harness is **work in progress** and likely to be massively reworked—see [clue-eval docs](docs/implementations/clue-eval.md).
