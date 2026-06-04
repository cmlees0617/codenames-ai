from clue_eval.boards.views import board_layout_to_spymaster_view


def test_board_layout_to_spymaster_view_blue_team():
    board = {
        "blues": ["ALPHA"],
        "reds": ["BRAVO"],
        "civilians": ["CHARLIE"],
        "assassins": ["DELTA"],
    }
    view = board_layout_to_spymaster_view(board, team="blue")
    assert view.team == "blue"
    by_word = {card.word: card.color for card in view.board}
    assert by_word["ALPHA"] == "blue"
    assert by_word["BRAVO"] == "red"
