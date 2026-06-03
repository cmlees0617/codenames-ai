import argparse

import pytest

from cno.cli import _normalize_args, build_parser
from cno.interactive import prompt_interactive
from cno.roles import default_nickname, parse_role


def test_parse_role_red_spymaster():
    team, role = parse_role("red-spymaster")
    assert team == "red"
    assert role == "spymasters"


def test_parse_role_underscore_alias():
    team, role = parse_role("blue_spymaster")
    assert team == "blue"
    assert role == "spymasters"


def test_default_nickname():
    assert default_nickname("red", "spymasters") == "RedSpymasterBot"
    assert default_nickname("blue", "operatives") == "BlueOperativeBot"


def test_parser_accepts_room_and_role():
    parser = build_parser()
    args = parser.parse_args(["halok-jonah", "red-spymaster"])
    assert args.room == "halok-jonah"
    assert args.role == ("red", "spymasters")


def test_parser_role_shorthand():
    parser = build_parser()
    args = parser.parse_args(["red-spymaster"])
    _normalize_args(args)
    assert args.room is None
    assert args.role == ("red", "spymasters")


def test_prompt_interactive_join_room(monkeypatch):
    selections = iter(["blue-spymaster"])
    texts = iter(["halok-jonah", ""])
    monkeypatch.setattr(
        "cno.interactive._select",
        lambda _title, _options: next(selections),
    )
    monkeypatch.setattr(
        "cno.interactive._text",
        lambda _title, **kwargs: next(texts),
    )

    args = prompt_interactive()

    assert args.room == "halok-jonah"
    assert args.role == ("blue", "spymasters")
    assert args.nickname == "BlueSpymasterBot"


def test_main_uses_interactive_when_no_argv(monkeypatch):
    import asyncio as asyncio_mod

    captured: dict[str, object] = {}
    real_run = asyncio_mod.run

    def fake_prompt() -> argparse.Namespace:
        return argparse.Namespace(
            room="demo-room",
            role=("red", "spymasters"),
            nickname="Bot",
            interactive=False,
            random_operative=False,
        )

    async def fake_async_main(args: object) -> int:
        captured["args"] = args
        return 0

    monkeypatch.setattr("cno.cli.prompt_interactive", fake_prompt)
    monkeypatch.setattr("cno.cli._async_main", fake_async_main)
    monkeypatch.setattr("cno.cli.asyncio.run", lambda coro: real_run(coro))

    from cno.cli import main

    with pytest.raises(SystemExit) as exc_info:
        main([])
    assert exc_info.value.code == 0
    assert captured["args"] is not None
