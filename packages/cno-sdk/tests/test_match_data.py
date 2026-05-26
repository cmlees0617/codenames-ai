from cno_sdk.match_data import parse_match_data, player_present
from cno_sdk.patches import apply_json_patches


def test_apply_json_patches_ignores_missing_remove():
    state = {
        "G": {
            "teams": {
                "red": {"spymasters": {"p#0": True}, "operatives": {}},
                "blue": {"spymasters": {}, "operatives": {}},
            }
        }
    }
    patches = [{"op": "remove", "path": "/G/teams/red/spymasters/p#7"}]
    updated = apply_json_patches(state, patches)
    assert updated["G"]["teams"]["red"]["spymasters"] == {"p#0": True}


def test_parse_match_data_from_list():
    raw = [
        {"id": 0, "name": "Alice", "isHost": True, "isConnected": True},
        {"id": 1},
    ]
    players = parse_match_data(raw)
    assert len(players) == 1
    assert players[0].name == "Alice"
    assert players[0].is_host is True


def test_player_present():
    raw = [{"name": "Alice"}, {}]
    assert player_present(raw, "0") is True
    assert player_present(raw, "1") is False
