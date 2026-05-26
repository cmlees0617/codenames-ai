import json
from pathlib import Path

from cno_sdk.session_log import PlayerSession, load_sessions, session_log_path


def test_load_sessions_empty(tmp_path: Path):
    assert load_sessions(path=tmp_path / "missing.jsonl") == []


def test_player_session_roundtrip(tmp_path: Path):
    log_file = tmp_path / "sessions.jsonl"
    record = PlayerSession(
        room="dumas-surip",
        match_id="abc123",
        player_id="3",
        credentials="foo-bar-baz",
        nickname="TestBot",
        host="https://example.com",
        socket_path="/2/socket.io",
        logged_at="2026-05-26T00:00:00+00:00",
    )
    log_file.write_text(json.dumps(record.__dict__) + "\n", encoding="utf-8")
    loaded = load_sessions(path=log_file)
    assert len(loaded) == 1
    assert loaded[0].credentials == "foo-bar-baz"
    assert session_log_path(log_file) == log_file
