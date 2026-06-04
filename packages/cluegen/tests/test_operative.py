from unittest.mock import patch

import numpy as np
from cluegen.operative import EmbeddingOperative, LLMOperative

# --- EMBEDDING OPERATIVE TESTS ---

@patch("cluegen.operative.SentenceTransformer")
def test_embedding_operative_guess(MockTransformer):
    """
    Tests that the EmbeddingOperative correctly uses cosine similarity 
    to find the closest words to the clue.
    """
    mock_model = MockTransformer.return_value
    
    # Create a deterministic mock vector map. 
    # We will make "APPLE" and "BANANA" geometrically close to "FRUIT", 
    # and "CAR" far away.
    vector_map = {
        "FRUIT": np.array([1.0, 0.0, 0.0]),
        "APPLE": np.array([0.9, 0.1, 0.0]),   # Very close to FRUIT
        "BANANA": np.array([0.8, 0.2, 0.0]),  # Close to FRUIT
        "CAR": np.array([0.0, 1.0, 0.0])      # Completely unrelated
    }
    
    # Tell our fake model to return the vectors from our map
    mock_model.encode.side_effect = lambda word: vector_map.get(word.upper(), np.array([0.0, 0.0, 1.0]))

    op = EmbeddingOperative(model_name="dummy-model")
    
    # 1. Test updating board state correctly caches the words
    op.update_board_state(["APPLE", "BANANA", "CAR"])
    assert len(op.word_embeddings) == 3
    assert "APPLE" in op.word_embeddings

    # 2. Test guessing functionality
    guesses = op.guess(clue="FRUIT", count=2)
    
    # It should pick APPLE and BANANA because their vectors are closest to FRUIT
    assert guesses == ["APPLE", "BANANA"]
    
    # 3. Test that it respects the count boundary (even if we ask for 5, it can only return 3)
    guesses = op.guess(clue="FRUIT", count=5)
    assert len(guesses) == 3


def test_embedding_operative_empty_state():
    """Tests the operative fails gracefully if the board is empty."""
    with patch("cluegen.operative.SentenceTransformer"):
        op = EmbeddingOperative()
        assert op.guess("CLUE", 2) == []


# --- LOCAL LLM OPERATIVE TESTS ---

@patch("transformers.pipeline")
def test_local_llm_operative_parsing(mock_pipeline):
    """
    Tests that the LocalLLMOperative correctly formats the prompt,
    parses the AI's comma-separated output, and filters hallucinations.
    """
    # Setup our fake Hugging Face pipeline
    mock_generator = mock_pipeline.return_value
    
    op = LLMOperative(model_name="dummy-model")
    op.update_board_state(["APPLE", "BANANA", "CAR", "DOG"])

    # --- Scenario 1: Perfect Output ---
    # The AI correctly guesses two words on the board
    mock_generator.return_value = [{'generated_text': "APPLE, CAR\n"}]
    
    guesses = op.guess("CLUE", count=2)
    assert guesses == ["APPLE", "CAR"]

    # --- Scenario 2: Hallucination Filtering ---
    # The AI guesses a word that is NOT on the board (e.g., PIZZA)
    mock_generator.return_value = [{'generated_text': "BANANA, PIZZA, DOG"}]
    
    guesses = op.guess("CLUE", count=3)
    
    # PIZZA should be filtered out because it isn't in visible_words
    assert "PIZZA" not in guesses
    assert guesses == ["BANANA", "DOG"]

    # --- Scenario 3: Respecting the Count ---
    # The AI gets overly excited and generates 4 words, but we only asked for 2
    mock_generator.return_value = [{'generated_text': "APPLE, BANANA, CAR, DOG"}]
    
    guesses = op.guess("CLUE", count=2)
    
    # It should chop the list down to exactly 2 words
    assert len(guesses) == 2
    assert guesses == ["APPLE", "BANANA"]