import pytest
from clue_eval.clues.legality import (
    is_legal_clue,
    validate_clue_legality,
)


@pytest.fixture(scope="module", autouse=True)
def _ensure_nltk_corpora():
    from clue_eval.clues.legality import _ensure_wordnet

    _ensure_wordnet()


def test_single_token_rules():
    visible = ["APPLE"]
    assert is_legal_clue("CAR", 1, visible)
    assert not is_legal_clue("", 1, visible)
    assert not is_legal_clue("   ", 1, visible)
    assert not is_legal_clue("TWO WORDS", 1, visible)


def test_min_count():
    visible = ["APPLE"]
    result = validate_clue_legality("CAR", 0, visible)
    assert not result.legal
    assert any(violation.rule == "min_count" for violation in result.violations)


def test_stem_and_substring_rules():
    visible = ["SNOWMAN", "WIFE", "APPLE"]
    assert is_legal_clue("CAR", 1, visible)
    assert is_legal_clue("ORANGE", 1, visible)
    assert not is_legal_clue("apple", 1, visible)
    assert not is_legal_clue("SNOW", 1, visible)
    assert not is_legal_clue("MAN", 1, visible)
    assert not is_legal_clue("WIVES", 1, visible)
    assert not is_legal_clue("SNOWMEN", 1, visible)


def test_homophone_rule(monkeypatch):
    def fake_codes(word: str) -> frozenset[str]:
        if word in {"NIGHT", "KNIGHT"}:
            return frozenset({"SHARED"})
        return frozenset()

    monkeypatch.setattr("clue_eval.clues.legality._double_metaphone_codes", fake_codes)
    visible = ["KNIGHT", "TABLE"]
    result = validate_clue_legality("NIGHT", 1, visible)
    assert not result.legal
    assert any(violation.rule == "homophone" for violation in result.violations)


def test_multiple_violations_reported():
    visible = ["APPLE"]
    result = validate_clue_legality("apple", 0, visible)
    assert not result.legal
    rules = {violation.rule for violation in result.violations}
    assert "min_count" in rules
    assert "stem_or_lemma" in rules
