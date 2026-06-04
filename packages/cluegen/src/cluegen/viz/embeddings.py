"""Plot board words and generated clues in embedding space (ClueEngine only)."""

from __future__ import annotations

import random
import warnings
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE

from cluegen.clue_engine import ClueEngine

warnings.filterwarnings("ignore", category=UserWarning)


def plot_board_and_clue(engine: ClueEngine, clue: dict[str, Any]) -> None:
    """Plot t-SNE projection of board embeddings, clue, and a vocab sample."""
    labels: list[str] = []
    vectors: list[np.ndarray] = []
    colors: list[str] = []
    visible_words = engine.visible_strings

    for word in visible_words:
        labels.append(word)
        vectors.append(engine.master_board_cache[word])
        if word in engine.target_strings:
            colors.append("green")
        elif word in engine.assassin_strings:
            colors.append("black")
        elif word in engine.enemy_strings:
            colors.append("red")
        else:
            colors.append("gray")

    clue_word = str(clue["word"])
    labels.append(f"CLUE: {clue_word}")
    vectors.append(engine.vocabulary[clue_word.lower()])
    colors.append("blue")

    vocab_sample = random.sample(list(engine.vocabulary.keys()), min(50, len(engine.vocabulary)))
    for word in vocab_sample:
        upper = word.upper()
        if upper not in visible_words and upper != clue_word.upper():
            labels.append(upper)
            vectors.append(engine.vocabulary[word])
            colors.append("lightgray")

    matrix = np.array(vectors)
    pca = PCA(n_components=min(50, len(vectors)), random_state=42)
    pca_result = pca.fit_transform(matrix)
    tsne = TSNE(n_components=2, perplexity=10, random_state=42)
    embeddings_2d = tsne.fit_transform(pca_result)

    plt.figure(figsize=(12, 8))
    for index, label in enumerate(labels):
        x, y = embeddings_2d[index, 0], embeddings_2d[index, 1]
        size = 100 if colors[index] != "lightgray" else 20
        plt.scatter(x, y, color=colors[index], s=size)
        if colors[index] != "lightgray":
            weight = "bold" if colors[index] == "blue" else "normal"
            plt.annotate(
                label,
                (x, y),
                xytext=(5, 5),
                textcoords="offset points",
                fontsize=10,
                fontweight=weight,
            )

    plt.title(f"Embedding Space (t-SNE) for Clue: {clue_word}", fontsize=16)
    plt.grid(True, linestyle="--", alpha=0.5)

    clue_idx = labels.index(f"CLUE: {clue_word}")
    for target in clue.get("intended_targets") or []:
        target_idx = labels.index(target)
        plt.plot(
            [embeddings_2d[clue_idx, 0], embeddings_2d[target_idx, 0]],
            [embeddings_2d[clue_idx, 1], embeddings_2d[target_idx, 1]],
            "b--",
            alpha=0.4,
        )

    plt.show()
