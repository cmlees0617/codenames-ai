# codenames-ai/packages/cluegen/src/cluegen/visualize.py

"""Utility functions for visualizing word embeddings."""

import warnings

import matplotlib.pyplot as plt
import numpy as np
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE

from cluegen.spymaster import Spymaster
from cluegen.utils import load_boards_from_json

warnings.filterwarnings('ignore')

def plot_board_and_clue(spymaster: Spymaster, clue: dict):
    """
    Takes an initialized Spymatster and its best clue and plots the vectors.

    Parameters:
        spymaster: An initialized Spymaster with a loaded vocabulary.
        clue: A dictionary containing the clue word and its associated target words.
    """
    labels = []
    vectors = []
    colors = []
    visible_words = spymaster.visible_strings

    # Inside plot_board_and_clue in visualize.py...
    for word in visible_words:
        vec = spymaster.master_board_cache[word]
        labels.append(word)
        vectors.append(vec)
        
        # Color code based on what type of card it is using the spymaster's string lists
        if word in spymaster.target_strings:
            colors.append("green")
        elif word in spymaster.assassin_strings:
            colors.append("black")
        elif word in spymaster.enemy_strings:
            colors.append("red")
        else:
            colors.append("gray")

    # Add the clue and its intended targets
    labels.append(f"CLUE: {clue['word']}")
    vectors.append(spymaster.vocabulary[clue['word'].lower()])
    colors.append("blue")

    # Add a random sample of background vocabulary to see the noise
    import random
    vocab_sample = random.sample(list(spymaster.vocabulary.keys()), 50)
    for word in vocab_sample:
        if word.upper() not in visible_words and word.upper() != clue['word'].upper():
            labels.append(word.upper())
            vectors.append(spymaster.vocabulary[word])
            colors.append("lightgray")

    # Dimensionality reduction using t-SNE (pre-filtered using PCA for stability)
    matrix = np.array(vectors)
    pca = PCA(n_components=min(50, len(vectors)), random_state=42)
    pca_result = pca.fit_transform(matrix)
    tsne = TSNE(n_components=2, perplexity=10, random_state=42)
    embeddings_2d = tsne.fit_transform(pca_result)

    # Plot
    plt.figure(figsize=(12, 8))
    for i, label in enumerate(labels):
        x, y = embeddings_2d[i, 0], embeddings_2d[i, 1]
        plt.scatter(x, y, color=colors[i], s=100 if colors[i] != "lightgray" else 20)
        
        # Only label the important words to avoid clutter
        if colors[i] != "lightgray":
            plt.annotate(label, (x, y), xytext=(5, 5), textcoords='offset points', 
                         fontsize=10, fontweight='bold' if colors[i] == "blue" else 'normal')

    plt.title(f"Embedding Space (t-SNE) for Clue: {clue['word']}", fontsize=16)
    plt.grid(True, linestyle='--', alpha=0.5)
    
    # Draw lines connecting the clue to its intended targets
    clue_idx = labels.index(f"CLUE: {clue['word']}")
    for target in clue['intended_targets']:
        target_idx = labels.index(target)
        plt.plot([embeddings_2d[clue_idx, 0], embeddings_2d[target_idx, 0]], 
                 [embeddings_2d[clue_idx, 1], embeddings_2d[target_idx, 1]], 
                 'b--', alpha=0.4)

    plt.show()


if __name__ == "__main__":
    # Setup test environment
    bot = Spymaster()
    
    # Use your existing data folder setup
    from pathlib import Path
    data_dir = Path(__file__).parent.parent.parent / "data"
    bot.load_vocabulary(str(data_dir / "advanced_vocab.txt"), verbose=True)
    
    # Load a mock board into the bot
    boards = load_boards_from_json(data_dir / "test_boards.json")
    board = boards[0]
    targets = board["blues"]
    civilians = board["civilians"]
    enemies = board["reds"]
    assassins = board["assassins"]
    bot.initialize_game_board(targets + civilians + enemies + assassins)
    bot.update_board_state(
        targets=targets,
        civilians=civilians,
        enemies=enemies,
        assassins=assassins,
    )
    
    # Generate the clue
    best_clue = bot.generate_clue(min_targets=1, max_targets=3, verbose=True)
    print(f"Generated Clue: {best_clue}")
    
    # Plot it
    plot_board_and_clue(bot, best_clue)