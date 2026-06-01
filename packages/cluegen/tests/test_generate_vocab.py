import pytest
from unittest.mock import patch
from cluegen.generate_vocab import generate_vocab

@patch("cluegen.generate_vocab.wordfreq")
def test_generate_vocab_filtering_and_accents(mock_wordfreq):
    """
    Tests that the script correctly filters out bad words, strips accents,
    and stops when the zipf_cutoff is reached.
    """
    # 1. Mock the dictionary list to return a controlled set of words
    mock_wordfreq.iter_wordlist.return_value = [
        "the",       # Stopword (should be skipped)
        "it",        # Too short (should be skipped)
        "cat123",    # Not alphabetical (should be skipped)
        "café",      # Accented (should become 'cafe')
        "naïve",     # Accented (should become 'naive')
        "apple",     # Valid standard word
        "rareword"   # Zipf score too low (should trigger the break)
    ]
    
    # 2. Mock the zipf_frequency scores to control the break point
    def mock_zipf(word, lang):
        scores = {
            "the": 8.0,
            "it": 7.5,
            "cat123": 6.0,
            "café": 5.0,
            "naïve": 4.5,
            "apple": 4.0,
            "rareword": 2.0  # This score will trigger the cutoff break
        }
        return scores.get(word, 0.0)
        
    mock_wordfreq.zipf_frequency.side_effect = mock_zipf
    
    # 3. Run the function with a cutoff of 3.0
    vocab = generate_vocab(zipf_cutoff=3.0)
    
    # 4. Verify the results
    # 'rareword' is <= 3.0, so the loop breaks BEFORE adding it.
    expected_vocab = ["cafe", "naive", "apple"]
    
    assert vocab == expected_vocab


@patch("cluegen.generate_vocab.wordfreq")
def test_generate_vocab_prevents_duplicates(mock_wordfreq):
    """
    Tests that if two different raw words normalize to the same base word
    (e.g., 'cafe' and 'café'), it is only added to the vocabulary once.
    """
    mock_wordfreq.iter_wordlist.return_value = [
        "cafe",      # Standard word
        "café",      # Will normalize to 'cafe'
        "breakword"  # Triggers break
    ]
    
    def mock_zipf(word, lang):
        if word == "breakword":
            return 1.0  # Trigger cutoff break
        return 5.0
        
    mock_wordfreq.zipf_frequency.side_effect = mock_zipf
    
    vocab = generate_vocab(zipf_cutoff=2.0)
    
    # "cafe" should only appear once
    assert vocab == ["cafe"]