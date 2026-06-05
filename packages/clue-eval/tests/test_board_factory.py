from pathlib import Path

import pytest
from clue_eval.boards.factory import BoardFactory


def test_create_random_game_distribution():
    pool = [f"WORD{i}" for i in range(30)]
    board = BoardFactory.create_random_game(pool)

    assert len(board["blues"]) == 9
    assert len(board["reds"]) == 8
    assert len(board["civilians"]) == 7
    assert len(board["assassins"]) == 1
    all_words = board["blues"] + board["reds"] + board["civilians"] + board["assassins"]
    assert len(all_words) == len(set(all_words))


def test_create_clue_set_respects_targets():
    pool = [f"WORD{i}" for i in range(30)]
    targets = ["WORD0", "WORD1", "WORD2"]
    board = BoardFactory.create_clue_set(targets, pool, civilian_count=5, enemy_count=5)

    assert board["blues"] == targets
    assert len(board["civilians"]) == 5
    assert len(board["reds"]) == 5
    assert len(board["assassins"]) == 1


def test_from_vocab_file(tmp_path: Path):
    vocab = tmp_path / "vocab.txt"
    vocab.write_text("alpha\nbeta\ngamma\ndelta\necho\n", encoding="utf-8")
    words = BoardFactory.from_vocab_file(vocab, count=3)
    assert len(words) == 3
    assert all(word.isupper() for word in words)


def test_from_vocab_file_raises_when_too_small(tmp_path: Path):
    vocab = tmp_path / "vocab.txt"
    vocab.write_text("only\n", encoding="utf-8")
    with pytest.raises(ValueError, match="only has"):
        BoardFactory.from_vocab_file(vocab, count=5)
