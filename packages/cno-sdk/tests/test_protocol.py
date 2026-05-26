import json
from pathlib import Path

import pytest

from cno_sdk.moves import build_give_clue, build_join_team
from cno_sdk.protocol import build_make_move
from cno_sdk.state import GameState, is_spymaster_turn, pick_friendly_words


FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def test_join_team_action_matches_fixture():
    fixture = load_fixture("join_team_update.json")
    expected = fixture["payload"][0]
    action = build_join_team(
        "red",
        "spymasters",
        player_id="0",
        credentials="rosilitu-hasumotu-luhoniba",
    )
    assert action == expected


def test_give_clue_action_matches_fixture():
    fixture = load_fixture("give_clue_update.json")
    expected = fixture["payload"][0]
    action = build_give_clue(
        "PINEAPPLE",
        "3",
        ["HEAVEN", "BULB", "CHICK"],
        player_id="0",
        credentials="rosilitu-hasumotu-luhoniba",
        player_name="SpymasterBot",
    )
    assert action == expected


def test_spymaster_turn_detection():
    fixture = load_fixture("sync_spymaster_turn.json")
    state = GameState.from_bgio(fixture["state"])
    assert is_spymaster_turn(state, "0", "red")
    assert not is_spymaster_turn(state, "1", "red")


def test_pick_friendly_words_prefers_hardcoded():
    fixture = load_fixture("sync_spymaster_turn.json")
    state = GameState.from_bgio(fixture["state"])
    words = pick_friendly_words(state, "red", ["HEAVEN", "BULB", "CHICK"], 3)
    assert words == ["HEAVEN", "BULB", "CHICK"]


def test_make_move_shape():
    action = build_make_move(
        "joinTeam",
        ["blue", "spymasters"],
        player_id="2",
        credentials="abc-def-ghi",
    )
    assert action["type"] == "MAKE_MOVE"
    assert action["payload"]["type"] == "joinTeam"
