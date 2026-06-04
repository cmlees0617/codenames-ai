from unittest.mock import patch

import numpy as np
import pytest
from cluegen.clue_engine import ClueEngine

# --- FIXTURES ---

@pytest.fixture
def clue_engine():
    """ClueEngine with mocked SentenceTransformer (no model download)."""
    with patch("cluegen.clue_engine.SentenceTransformer") as MockTransformer:
        mock_model = MockTransformer.return_value
        mock_model.encode.side_effect = lambda word: np.random.rand(384)
        return ClueEngine(model_name="test-model")


# --- TESTS ---

def test_is_legal_clue(clue_engine):
    """ 
    Test the substring and stemming legality checks.
    """
    visible_words = ["SNOWMAN", "WIFE", "APPLE"]

    # Valid clues
    assert clue_engine.is_legal_clue("CAR", visible_words) == True
    assert clue_engine.is_legal_clue("ORANGE", visible_words) == True

    # Exact match 
    assert clue_engine.is_legal_clue("apple", visible_words) == False
    assert clue_engine.is_legal_clue("APPLE", visible_words) == False

    # Substring match
    assert clue_engine.is_legal_clue("SNOW", visible_words) == False
    assert clue_engine.is_legal_clue("MAN", visible_words) == False

    # Stemmed / Morphological match
    assert clue_engine.is_legal_clue("WIVES", visible_words) == False
    assert clue_engine.is_legal_clue("SNOWMEN", visible_words) == False


def test_board_initialization_and_update(clue_engine):
    """
    Test that the board correctly caches vectors and updates states.
    """
    board_words = ["ALPHA", "BRAVO", "CHARLIE", "DELTA"]

    clue_engine.initialize_game_board(board_words)
    assert "ALPHA" in clue_engine.master_board_cache
    assert len(clue_engine.master_board_cache) == 4

    # Update the active state
    clue_engine.update_board_state(
        targets=["ALPHA"], 
        civilians=["BRAVO"], 
        enemies=["CHARLIE"], 
        assassins=["DELTA"]
    )

    assert clue_engine.board_state["is_initialized"] == True
    assert len(clue_engine.target_strings) == 1
    assert "ALPHA" in clue_engine.target_strings
    assert len(clue_engine.visible_strings) == 4


def test_update_board_state_errors(clue_engine):
    """
    Test that updating the board fails safely on bad input.
    """
    # Fails if master cache wasn't initialized
    with pytest.raises(ValueError, match="Master cache is empty"):
        clue_engine.update_board_state(["A"], ["B"], ["C"], ["D"])
        
    clue_engine.initialize_game_board(["ALPHA", "BRAVO"])
    
    # Fails if we pass a word that wasn't in the initial setup
    with pytest.raises(ValueError, match="not found in master board cache"):
        clue_engine.update_board_state(["CHARLIE"], [], [], [])


def test_generate_clue_validations(clue_engine):
    """
    Test that the engine catches bad generation parameters.
    """
    # Fails if vocab is empty
    with pytest.raises(ValueError, match="Vocabulary is empty"):
        clue_engine.generate_clue()
        
    # Mock a basic vocab
    clue_engine.vocabulary = {"TEST": np.random.rand(384)}
    
    # Fails if board isn't initialized
    with pytest.raises(ValueError, match="Board state not initialized"):
        clue_engine.generate_clue()
        
    # Setup board
    clue_engine.initialize_game_board(["TARGET1", "TARGET2"])
    clue_engine.update_board_state(["TARGET1", "TARGET2"], [], [], [])
    
    # Fails if targets bounds are illogical
    with pytest.raises(ValueError, match="min_targets cannot be greater than max_targets"):
        clue_engine.generate_clue(min_targets=3, max_targets=2)
        
    with pytest.raises(ValueError, match="groups of size < 1"):
        clue_engine.generate_clue(min_targets=0, max_targets=0)


def test_generate_clue_success(clue_engine):
    """
    Test the end-to-end clue generation loop with mocked vectors.
    """
    clue_engine.vocabulary = {
        "DOG": np.random.rand(384),
        "CAT": np.random.rand(384)
    }
    
    clue_engine.initialize_game_board(["BONE", "MOUSE", "CAR", "BOMB"])
    clue_engine.update_board_state(
        targets=["BONE", "MOUSE"],
        civilians=["CAR"],
        enemies=[],
        assassins=["BOMB"]
    )
    
    clue = clue_engine.generate_clue(min_targets=1, max_targets=2)
    
    # Check return structure
    assert isinstance(clue, dict)
    assert clue["word"] in ["DOG", "CAT"]
    assert isinstance(clue["score"], float)
    assert isinstance(clue["intended_targets"], list)


def test_load_vocabulary_creates_cache(clue_engine, tmp_path):
    """
    Test that reading a .txt file successfully generates a model-specific .pkl cache.
    """
    # tmp_path is a built-in pytest fixture that provides a temporary directory
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    txt_file = data_dir / "test_vocab.txt"
    txt_file.write_text("APPLE\nBANANA\n")
    
    clue_engine.load_vocabulary(str(txt_file))
    
    assert len(clue_engine.vocabulary) == 2
    assert "apple" in clue_engine.vocabulary
    
    # Check that the pickle cache file was created with the sanitized model name
    expected_cache_file = data_dir / "test_vocab_test-model.pkl"
    assert expected_cache_file.exists()


def test_prune_vocabulary(clue_engine):
    """Test that vocabulary is safely reduced."""
    # Create fake vocab
    clue_engine.vocabulary = {
        "GOOD_WORD": np.array([1.0, 0.0]), # Will match target
        "BAD_WORD": np.array([0.0, 1.0])   # Will match assassin
    }
    
    # Create a 2D dummy board state to test matrix math
    clue_engine.board_state["targets"] = [np.array([1.0, 0.0])]
    clue_engine.board_state["assassins"] = [np.array([0.0, 1.0])]
    clue_engine.board_state["enemies"] = []
    
    # Prune
    clue_engine.prune_vocabulary(danger_threshold=0.5, relevance_threshold=0.5)
    
    # Only GOOD_WORD should remain
    assert "GOOD_WORD" in clue_engine.vocabulary
    assert "BAD_WORD" not in clue_engine.vocabulary