# packages/cluegen/src/cluegen/operative.py

from abc import ABC, abstractmethod

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class GuessEngine(ABC):
    """Internal batch-guess engine (used by ``EmbeddingGuessAlgorithm``)."""
    def __init__(self):
        self.visible_words: list[str] = []

    def update_board_state(self, visible_words: list[str]) -> None:
        """
        Update the operative's knowledge of the visible words on the board.

        Parameters:
            visible_words: A list of the currently visible words on the board.
        """
        self.visible_words = visible_words

    @abstractmethod
    def guess(self, clue: str, count: int) -> list[str]:
        """
        Given a clue and a count, return a list of guessed words.

        Parameters:
            clue: The clue word provided by the spymaster.
            count: The number of words the spymaster indicated are related to the clue.
        """
        pass


class EmbeddingGuessEngine(GuessEngine):
    """
    Uses local vector embeddings to find the closest words to the clue.
    """
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        super().__init__()
        print(f"Loading operative embedding model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        self.word_embeddings: dict[str, np.ndarray] = {}

    def update_board_state(self, visible_words):
        super().update_board_state(visible_words)

        # Embed and cache words we haven't seen before
        for word in self.visible_words:
            if word not in self.word_embeddings:
                self.word_embeddings[word] = self.model.encode(word)

    def guess(self, clue: str, count: int) -> list[str]:
        if not self.visible_words or count < 1: return[]

        # Ensure we don't guess more words than are visible
        count = min(count, len(self.visible_words))

        # Embed the clue
        clue_vec = self.model.encode(clue).reshape(1, -1)

        # Get embeddings for all currently visible words
        board_vecs = np.array([self.word_embeddings[word] for word in self.visible_words])

        # Calculate cosine similarity
        sims = cosine_similarity(clue_vec, board_vecs)[0]

        # Get indices of the top most similar words
        top_indices = sims.argsort()[-count:][::-1]

        return [self.visible_words[i] for i in top_indices]
    

class LLMGuessEngine(GuessEngine):
    """
    Uses a small, local open-source LLM to reason about the board 
    without needing any API keys.
    """
    def __init__(self, model_name: str = "Qwen/Qwen2.5-0.5B-Instruct"):
        super().__init__()
        import warnings

        from transformers import pipeline
        warnings.filterwarnings('ignore') # Suppress verbose Hugging Face warnings
        
        print(f"Loading local LLM '{model_name}' (this may take a minute on the first run)...")
        # pipeline automatically handles downloading and executing the model
        self.generator = pipeline(
            "text-generation", 
            model=model_name, 
            device_map="auto" # Will automatically use your GPU if you have one, else CPU
        )

    def update_board_state(self, visible_words):
        super().update_board_state(visible_words)

    def guess(self, clue: str, count: int) -> list[str]:
        if not self.visible_words or count < 1:
            return []

        count = min(count, len(self.visible_words))

        # Small local models need extremely direct and simple prompts
        prompt = (
            f"You are playing Codenames. The available words on the board are: {', '.join(self.visible_words)}.\n"
            f"The clue is '{clue}'.\n"
            f"Select the {count} words from the board that best match the clue.\n"
            f"Output ONLY the words, separated by commas, and nothing else."
        )
        
        # Format the prompt into the chat template the model expects
        messages = [{"role": "user", "content": prompt}]
        
        # Generate the response
        output = self.generator(
            messages, 
            max_new_tokens=20,     # We only need a few words, so stop generating quickly
            do_sample=False,       # Keep it deterministic (no random guessing)
            return_full_text=False # Return only the AI's answer, not our prompt
        )
        
        response_text = output[0]['generated_text']
        print(f"[LLM Output] {response_text.strip()}") # Useful for debugging!
        
        # Clean up the output in case the LLM used weird formatting
        raw_guesses = [w.strip().upper() for w in response_text.replace('\n', ',').split(',')]
        
        # Filter out hallucinations (words the AI invented that aren't on the board)
        valid_guesses = [w for w in raw_guesses if w in self.visible_words]
        
        return valid_guesses[:count]