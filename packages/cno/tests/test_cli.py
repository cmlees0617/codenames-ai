from cno.cli import parse_role, build_parser


def test_parse_role_red_spymaster():
    team, role = parse_role("red-spymaster")
    assert team == "red"
    assert role == "spymasters"


def test_parse_role_underscore_alias():
    team, role = parse_role("blue_spymaster")
    assert team == "blue"
    assert role == "spymasters"


def test_parser_accepts_room_and_role():
    parser = build_parser()
    args = parser.parse_args(["halok-jonah", "red-spymaster"])
    assert args.room == "halok-jonah"
    assert args.role == ("red", "spymasters")
