import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch
from cluegen.spymaster import Spymaster

# --- FIXTURES ---

@pytest.fixture
def spymaster():
    """
    Returns a CodenamesSpymaster with a mocked SentenceTransformer so tests
    run instantly without downloading gigabytes of ML models.
    """
    with patch("cluegen.spymaster.SentenceTransformer") as MockTransformer:
        # Create a mock model that returns a random 384-dimensional array for any word
        mock_model = MockTransformer.return_value
        mock_model.encode.side_effect = lambda word: np.random.rand(384)
        
        bot = Spymaster(model_name="test-model")
        return bot


# --- TESTS ---

def test_is_legal_clue(spymaster):
    """ 
    Test the substring and stemming legality checks.
    """
    visible_words = ["SNOWMAN", "WIFE", "APPLE"]

    # Valid clues
    assert spymaster.is_legal_clue("CAR", visible_words) == True
    assert spymaster.is_legal_clue("ORANGE", visible_words) == True

    # Exact match 
    assert spymaster.is_legal_clue("apple", visible_words) == False
    assert spymaster.is_legal_clue("APPLE", visible_words) == False

    # Substring match
    assert spymaster.is_legal_clue("SNOW", visible_words) == False
    assert spymaster.is_legal_clue("MAN", visible_words) == False

    # Stemmed / Morphological match
    assert spymaster.is_legal_clue("WIVES", visible_words) == False
    assert spymaster.is_legal_clue("SNOWMEN", visible_words) == False


def test_board_initialization_and_update(spymaster):
    """
    Test that the board correctly caches vectors and updates states.
    """
    board_words = ["ALPHA", "BRAVO", "CHARLIE", "DELTA"]

    spymaster.initialize_game_board(board_words)
    assert "ALPHA" in spymaster.master_board_cache
    assert len(spymaster.master_board_cache) == 4

    # Update the active state
    spymaster.update_board_state(
        targets=["ALPHA"], 
        civilians=["BRAVO"], 
        enemies=["CHARLIE"], 
        assassins=["DELTA"]
    )

    assert spymaster.board_state["is_initialized"] == True
    assert len(spymaster.target_strings) == 1
    assert "ALPHA" in spymaster.target_strings
    assert len(spymaster.visible_strings) == 4


def test_update_board_state_errors(spymaster):
    """
    Test that updating the board fails safely on bad input.
    """
    # Fails if master cache wasn't initialized
    with pytest.raises(ValueError, match="Master cache is empty"):
        spymaster.update_board_state(["A"], ["B"], ["C"], ["D"])
        
    spymaster.initialize_game_board(["ALPHA", "BRAVO"])
    
    # Fails if we pass a word that wasn't in the initial setup
    with pytest.raises(ValueError, match="not found in master board cache"):
        spymaster.update_board_state(["CHARLIE"], [], [], [])


def test_generate_clue_validations(spymaster):
    """
    Test that the engine catches bad generation parameters.
    """
    # Fails if vocab is empty
    with pytest.raises(ValueError, match="Vocabulary is empty"):
        spymaster.generate_clue()
        
    # Mock a basic vocab
    spymaster.vocabulary = {"TEST": np.random.rand(384)}
    
    # Fails if board isn't initialized
    with pytest.raises(ValueError, match="Board state not initialized"):
        spymaster.generate_clue()
        
    # Setup board
    spymaster.initialize_game_board(["TARGET1", "TARGET2"])
    spymaster.update_board_state(["TARGET1", "TARGET2"], [], [], [])
    
    # Fails if targets bounds are illogical
    with pytest.raises(ValueError, match="min_targets cannot be greater than max_targets"):
        spymaster.generate_clue(min_targets=3, max_targets=2)
        
    with pytest.raises(ValueError, match="groups of size < 1"):
        spymaster.generate_clue(min_targets=0, max_targets=0)


def test_generate_clue_success(spymaster):
    """
    Test the end-to-end clue generation loop with mocked vectors.
    """
    spymaster.vocabulary = {
        "DOG": np.random.rand(384),
        "CAT": np.random.rand(384)
    }
    
    spymaster.initialize_game_board(["BONE", "MOUSE", "CAR", "BOMB"])
    spymaster.update_board_state(
        targets=["BONE", "MOUSE"],
        civilians=["CAR"],
        enemies=[],
        assassins=["BOMB"]
    )
    
    clue = spymaster.generate_clue(min_targets=1, max_targets=2)
    
    # Check return structure
    assert isinstance(clue, dict)
    assert clue["word"] in ["DOG", "CAT"]
    assert isinstance(clue["score"], float)
    assert isinstance(clue["intended_targets"], list)


def test_load_vocabulary_creates_cache(spymaster, tmp_path):
    """
    Test that reading a .txt file successfully generates a model-specific .pkl cache.
    """
    # tmp_path is a built-in pytest fixture that provides a temporary directory
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    txt_file = data_dir / "test_vocab.txt"
    txt_file.write_text("APPLE\nBANANA\n")
    
    spymaster.load_vocabulary(str(txt_file))
    
    assert len(spymaster.vocabulary) == 2
    assert "apple" in spymaster.vocabulary
    
    # Check that the pickle cache file was created with the sanitized model name
    expected_cache_file = data_dir / "test_vocab_test-model.pkl"
    assert expected_cache_file.exists()


def test_prune_vocabulary(spymaster):
    """Test that vocabulary is safely reduced."""
    # Create fake vocab
    spymaster.vocabulary = {
        "GOOD_WORD": np.array([1.0, 0.0]), # Will match target
        "BAD_WORD": np.array([0.0, 1.0])   # Will match assassin
    }
    
    # Create a 2D dummy board state to test matrix math
    spymaster.board_state["targets"] = [np.array([1.0, 0.0])]
    spymaster.board_state["assassins"] = [np.array([0.0, 1.0])]
    spymaster.board_state["enemies"] = []
    
    # Prune
    spymaster.prune_vocabulary(danger_threshold=0.5, relevance_threshold=0.5)
    
    # Only GOOD_WORD should remain
    assert "GOOD_WORD" in spymaster.vocabulary
    assert "BAD_WORD" not in spymaster.vocabulary