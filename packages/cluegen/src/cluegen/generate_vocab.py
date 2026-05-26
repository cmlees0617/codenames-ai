# src/generate_vocab.py
# FIXME: Eliminate stop words

import wordfreq
from pathlib import Path
import nltk
from nltk.corpus import stopwords
import ssl

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# Downlaod stopwords
nltk.download('stopwords', quiet=True)
STOP_WORDS = set(stopwords.words('english'))


def generate_vocab(zipf_cutoff: float) -> list[str]:
    """
    Generates a list of words in the English vocabulary that fall above the given
    Zipf frequency threshold.
    """
    vocab = []

    for word in wordfreq.iter_wordlist('en'):
        if len(word) < 3 or not word.isalpha() or word in STOP_WORDS:
            continue

        score = wordfreq.zipf_frequency(word, 'en')

        # iter_wordlist goes from most to least common
        if score <= zipf_cutoff:
            break
         
        vocab.append(word)

    return vocab
        

def main():
    # 1. Resolve paths: Get the directory of this script (src/), then find data/
    SCRIPT_DIR = Path(__file__).parent
    DATA_DIR = SCRIPT_DIR.parent / "data"
    
    # Ensure the data directory exists before trying to write to it
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Generate SIMPLE, STANDARD, and ADVANCED vocabularies
    zipf_cutoffs = {
        "simple": 4.5,
        "standard": 3.5,
        "advanced": 2.5
    }

    for name, cutoff in zipf_cutoffs.items():
        print(f"Generating {name} vocabulary...")
        vocab_list = generate_vocab(cutoff)
        
        # 2. Save directly into the data folder
        filename = DATA_DIR / f"{name}_vocab.txt"
        with open(filename, 'w', encoding="utf-8") as f:
            for word in vocab_list:
                f.write(f"{word.upper()}\n")
        
        print(f"Saved {len(vocab_list)} words to {filename}")

if __name__ == "__main__":
    main()