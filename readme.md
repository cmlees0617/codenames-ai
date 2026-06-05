# codenames-ai

Python monorepo for [Codenames Online](https://codenames.game) bots: wire client, CLI, and offline clue generation.

**Documentation:** https://cmlees0617.github.io/codenames-ai/

```bash
uv sync --all-packages --group dev
uv run cno                          # join a live room
uv run python -m cluegen             # optional embedding example
uv run python packages/clue-eval/examples/generate_standard_board_set.py  # benchmark boards
```
