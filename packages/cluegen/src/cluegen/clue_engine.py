# algos.py

import itertools
import pickle
import ssl
from pathlib import Path

import nltk
import numpy as np
from nltk.stem import SnowballStemmer, WordNetLemmatizer
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Download WordNet for lemmatization
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

nltk.download('wordnet', quiet=True)


class ClueEngine:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Download selected model and initialize state variables.
        """
        print(f"Loading embedding model '{model_name}'...")
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

        # The global vocabulary the AI is allowed to use for clues
        self.vocabulary: dict = {}
        self.stemmer = SnowballStemmer("english")
        self.lemmatizer = WordNetLemmatizer()

        # Stores vectors for all 25 words (should not be modified after initialization)
        self.master_board_cache: dict[str, np.ndarray] = {}

        # The ACTIVE board state (updates every turn as cards get guessed)
        self.board_state = {
            "targets": [],   # List of vectors
            "civilians": [], # List of vectors
            "enemies": [],   # List of vectors
            "assassins": [], # List of vectors
            "is_initialized": False
        }
        
        # Raw strings of the active board (used for legality checks and output)
        self.target_strings: list[str] = []
        self.assassin_strings: list[str] = []
        self.enemy_strings: list[str] = []
        self.civilian_strings: list[str] = []
        self.visible_strings: list[str] = []

    def load_vocabulary(self, filepath: str, verbose: bool = False):
        """
        Reads a vocabulary file. If a pre-computed pickle file exists, loads that.
        Otherwise, computes the embeddings and saves them to a pickle file for next time.
        """
        # Sanitize the model name
        safe_model_name = self.model_name.replace("/", "-").replace("\\", "-")

        # Create a model-specific cache path
        original_path = Path(filepath)
        cache_filename = f"{original_path.stem}_{safe_model_name}.pkl"
        cache_path = original_path.parent / cache_filename
        
        # Try to load from cache
        if Path(cache_path).exists():
            if verbose:
                print(f"Loading cached embeddings from {cache_path}...")
            with open(cache_path, 'rb') as f:
                self.vocabulary = pickle.load(f)
            print(f"Loaded {len(self.vocabulary)} words from cache.")
            return

        # Compute embeddings if no cache exists
        with open(filepath, encoding='utf-8') as file:
            vocab_list = [line.strip().lower() for line in file if line.strip()]
            for i, word in enumerate(vocab_list):
                if verbose:
                    print(f"\rLearning word {i + 1} of {len(vocab_list)}...", end="", flush=True)
                self.vocabulary[word] = self.encode_word(word)
                
        print(f"\nLoaded {len(self.vocabulary)} words into vocabulary.")
        
        # Save the newly computed embeddings to cache
        if verbose:
            print(f"Saving embeddings to {cache_path}...")
        with open(cache_path, 'wb') as f:
            pickle.dump(self.vocabulary, f)

    def prune_vocabulary(self, danger_threshold: float = 0.25, relevance_threshold: float = 0.1):
        """
        Filters vocabulary to keep only words that are safe and relevant using 
        vectorized matrix multiplication.
        """
        if not self.vocabulary or not self.board_state["targets"]:
            print("Cannot prune: Vocabulary or targets are empty.")
            return

        words = list(self.vocabulary.keys())
        vocab_matrix = np.array(list(self.vocabulary.values()))
        target_matrix = np.array(self.board_state["targets"])
        
        bad_vectors = self.board_state["enemies"] + self.board_state["assassins"]

        # Calculate max similarity to any target for all words at once
        target_sims = cosine_similarity(vocab_matrix, target_matrix)
        max_target_sim = target_sims.max(axis=1)
        
        # Calculate max similarity to any bad card for all words at once
        if bad_vectors:
            bad_matrix = np.array(bad_vectors)
            bad_sims = cosine_similarity(vocab_matrix, bad_matrix)
            max_bad_sim = bad_sims.max(axis=1)
        else:
            max_bad_sim = np.zeros(len(words))
            
        # Create boolean masks to filter the vocabulary
        safe_mask = max_bad_sim <= danger_threshold
        relevant_mask = max_target_sim >= relevance_threshold
        keep_mask = safe_mask & relevant_mask
        
        # Reconstruct the dictionary using the kept indices
        pruned = {words[i]: vocab_matrix[i] for i in range(len(words)) if keep_mask[i]}
            
        print(f"Vocabulary pruned: {len(self.vocabulary)} -> {len(pruned)} candidates.")
        self.vocabulary = pruned

    def encode_word(self, word: str) -> np.ndarray:
        """
        Helper method to encode a single word.
        """
        return self.model.encode(word)

    def initialize_game_board(self, all_board_words: list[str]):
        """
        Call this once at the start of the game. 
        """
        print("Encoding initial board state...")
        for word in all_board_words:
            word_upper = word.upper()
            if word_upper not in self.master_board_cache:
                self.master_board_cache[word_upper] = self.encode_word(word_upper)
        print("Board caching complete.")

    def update_board_state(self, targets: list[str], civilians: list[str], enemies: list[str], assassins: list[str]):
        """
        Call this at the start of every turn.
        Updates the current board state using dictionary lookups.
        """
        if not self.master_board_cache:
            raise ValueError("Master cache is empty. Call initialize_game_board() first.")

        # Save raw strings for legality checking and generation loops
        self.target_strings = [t.upper() for t in targets]
        self.civilian_strings = [c.upper() for c in civilians]
        self.enemy_strings = [e.upper() for e in enemies] 
        self.assassin_strings = [a.upper() for a in assassins]
        self.visible_strings = [w.upper() for w in (targets + civilians + enemies + assassins)]
        
        # Pull vectors instantly from the cache
        try:
            self.board_state["targets"] = [self.master_board_cache[t] for t in self.target_strings]
            self.board_state["civilians"] = [self.master_board_cache[c.upper()] for c in civilians]
            self.board_state["enemies"] = [self.master_board_cache[e.upper()] for e in enemies]
            self.board_state["assassins"] = [self.master_board_cache[a.upper()] for a in assassins]
            self.board_state["is_initialized"] = True
        except KeyError as e:
            raise ValueError(f"Word {e} not found in master board cache. Did you pass all words to initialize_game_board()?")

    def is_legal_clue(self, candidate: str, visible_board_words: list[str]) -> bool:
        """
        Ensures the clue isn't a morphological variant or substring of any visible board word.
        """
        candidate_lower = candidate.lower()
        candidate_stem = self.stemmer.stem(candidate_lower)
        candidate_lemma = self.lemmatizer.lemmatize(candidate_lower)

        for word in visible_board_words:
            word_lower = word.lower()
            word_stem = self.stemmer.stem(word_lower)
            word_lemma = self.lemmatizer.lemmatize(word_lower)

            # Check raw strings (catches simple substrings like "snow" in "snowman")
            if candidate_lower in word_lower or word_lower in candidate_lower:
                return False
            
            # Check stemmed strings (catches morphological variants like "wives" vs "wife")
            if candidate_stem in word_stem or word_stem in candidate_stem:
                return False
            
            # Check lemmatized strings (catches irregulars like "wives" vs "wife")
            if candidate_lemma in word_lemma or word_lemma in candidate_lemma:
                return False

        return True

    def generate_clue(self, min_targets: int = 1, max_targets: int = 3, size_bonus: float = 0.15, alpha: float = 0.2, beta: float = 0.4, gamma: float = 1.0, verbose: bool = False) -> dict:
        """
        Iterates through combinations of targets to find the best clue using 
        vectorized array calculations for maximum performance.
        """
        if not self.vocabulary:
            raise ValueError("Vocabulary is empty. Call load_vocabulary() first.")
        if not self.board_state["is_initialized"]:
            raise ValueError("Board state not initialized. Call update_board_state() first.")
            
        best_clue = {"word": None, "score": -999.0, "intended_targets": []}
        max_search_size = min(max_targets, len(self.target_strings))

        if max_search_size < 1:
            raise ValueError("Cannot search for groups of size < 1.")
        if min_targets > max_search_size:
            raise ValueError("min_targets cannot be greater than max_targets.")
        
        # Filter out illegal substring clues upfront to build our active candidate matrix
        legal_words = []
        legal_vectors = []
        for word, vec in self.vocabulary.items():
            if self.is_legal_clue(word, self.visible_strings):
                legal_words.append(word)
                legal_vectors.append(vec)
                
        if not legal_words:
            raise ValueError("No legal words left in vocabulary.")
            
        legal_matrix = np.array(legal_vectors)
        
        # Calculate Negative Penalties ONCE for all legal words
        def get_max_sims(board_key):
            vectors = self.board_state[board_key]
            if not vectors:
                return np.zeros(len(legal_words))
            neg_matrix = np.array(vectors)
            sims = cosine_similarity(legal_matrix, neg_matrix)
            return sims.max(axis=1)

        max_civ = get_max_sims("civilians")
        max_enemy = get_max_sims("enemies")
        max_assassin = get_max_sims("assassins")
        
        # Pre-computed array of penalties for every candidate word
        penalty_array = (alpha * max_civ) + (beta * max_enemy) + (gamma * max_assassin)
        target_matrix_full = np.array(self.board_state["targets"])
        
        # Search through combinations of targets and compute scores
        target_indices = range(len(self.target_strings))
        for group_size in range(min_targets, max_search_size + 1):
            
            if verbose:
                print(f"Considering groups of size {group_size}...")

            index_groups = list(itertools.combinations(target_indices, group_size))
            
            for i, group in enumerate(index_groups):
                group_indices = list(group)
                dummy_matrix = target_matrix_full[group_indices]
                dummy_strings = [self.target_strings[i] for i in group]

                # Compute similarity of all legal words to this specific target combination
                target_sims = cosine_similarity(legal_matrix, dummy_matrix)
                min_target = target_sims.min(axis=1) 
                avg_target = target_sims.mean(axis=1)
                blended_target_score = (min_target + avg_target) / 2
                
                # Formula: Base Score - Penalties + Size Bonus
                adjusted_scores = blended_target_score - penalty_array + ((group_size - 2) * size_bonus)
                
                # Find the single best word for this combination
                best_idx = np.argmax(adjusted_scores)
                best_score = adjusted_scores[best_idx]
                
                
                # Track the ultimate best clue
                if best_score > best_clue["score"]:
                    best_clue = {
                        "word": legal_words[best_idx].upper(),
                        "score": float(best_score),
                        "intended_targets": dummy_strings
                    }
                    
                    if verbose:
                        print(f"\tBest Clue Yet: {best_clue}")
                        
        return best_clue

    def generate_ranked_clues(
        self,
        min_targets: int = 1,
        max_targets: int = 3,
        *,
        limit: int = 10,
        size_bonus: float = 0.15,
        alpha: float = 0.2,
        beta: float = 0.4,
        gamma: float = 1.0,
    ) -> list[dict]:
        """Return up to ``limit`` distinct clues sorted by score (best first)."""
        if not self.vocabulary:
            raise ValueError("Vocabulary is empty. Call load_vocabulary() first.")
        if not self.board_state["is_initialized"]:
            raise ValueError("Board state not initialized. Call update_board_state() first.")

        max_search_size = min(max_targets, len(self.target_strings))
        if max_search_size < 1:
            raise ValueError("Cannot search for groups of size < 1.")
        if min_targets > max_search_size:
            raise ValueError("min_targets cannot be greater than max_targets.")

        legal_words = []
        legal_vectors = []
        for word, vec in self.vocabulary.items():
            if self.is_legal_clue(word, self.visible_strings):
                legal_words.append(word)
                legal_vectors.append(vec)

        if not legal_words:
            raise ValueError("No legal words left in vocabulary.")

        legal_matrix = np.array(legal_vectors)

        def get_max_sims(board_key):
            vectors = self.board_state[board_key]
            if not vectors:
                return np.zeros(len(legal_words))
            neg_matrix = np.array(vectors)
            sims = cosine_similarity(legal_matrix, neg_matrix)
            return sims.max(axis=1)

        max_civ = get_max_sims("civilians")
        max_enemy = get_max_sims("enemies")
        max_assassin = get_max_sims("assassins")
        penalty_array = (alpha * max_civ) + (beta * max_enemy) + (gamma * max_assassin)
        target_matrix_full = np.array(self.board_state["targets"])

        candidates: dict[str, dict] = {}
        target_indices = range(len(self.target_strings))
        for group_size in range(min_targets, max_search_size + 1):
            for group in itertools.combinations(target_indices, group_size):
                group_indices = list(group)
                dummy_matrix = target_matrix_full[group_indices]
                dummy_strings = [self.target_strings[i] for i in group_indices]
                target_sims = cosine_similarity(legal_matrix, dummy_matrix)
                min_target = target_sims.min(axis=1)
                avg_target = target_sims.mean(axis=1)
                blended_target_score = (min_target + avg_target) / 2
                adjusted_scores = (
                    blended_target_score - penalty_array + ((group_size - 2) * size_bonus)
                )
                for idx, score in enumerate(adjusted_scores):
                    word = legal_words[idx].upper()
                    entry = {
                        "word": word,
                        "score": float(score),
                        "intended_targets": dummy_strings,
                    }
                    if word not in candidates or score > candidates[word]["score"]:
                        candidates[word] = entry

        ranked = sorted(candidates.values(), key=lambda item: item["score"], reverse=True)
        return ranked[:limit]