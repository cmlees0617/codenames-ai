from cno_sdk.patches import apply_json_patches


def test_apply_join_team_patch():
    state = {
        "_stateID": 1,
        "G": {
            "teams": {
                "red": {"operatives": {}, "spymasters": {}},
                "blue": {"operatives": {}, "spymasters": {}},
            }
        },
        "ctx": {"phase": "lobby"},
    }
    patches = [
        {"op": "replace", "path": "/_stateID", "value": 2},
        {"op": "add", "path": "/G/teams/red/spymasters/p#0", "value": True},
    ]
    updated = apply_json_patches(state, patches)
    assert updated["_stateID"] == 2
    assert updated["G"]["teams"]["red"]["spymasters"]["p#0"] is True
