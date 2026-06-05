"""Load and save packaged word embedding matrices."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from clue_eval.paths import default_embeddings_path

MODEL_NAME = "glove-wiki-gigaword-300"
VECTOR_SIZE = 300
DEFAULT_FILENAME = "glove-wiki-gigaword-300.npz"


def load_words_from_file(path: Path) -> list[str]:
    """Load uppercase Codenames words (one per line)."""
    with path.open(encoding="utf-8") as handle:
        return [line.strip().upper() for line in handle if line.strip()]


@dataclass(frozen=True, slots=True)
class EmbeddingStore:
    """In-memory embeddings for the Codenames ``words.txt`` list."""

    words: tuple[str, ...]
    vectors: np.ndarray
    model: str
    missing_words: tuple[str, ...]

    @property
    def dimension(self) -> int:
        return int(self.vectors.shape[1])

    def vector_for(self, word: str) -> np.ndarray:
        """Return the embedding for ``word`` (case-insensitive)."""
        key = word.strip().upper()
        try:
            index = self.words.index(key)
        except ValueError as exc:
            raise KeyError(f"No embedding for {word!r}") from exc
        return self.vectors[index]

    @classmethod
    def load(cls, path: Path | None = None) -> EmbeddingStore:
        archive = np.load(path or default_embeddings_path(), allow_pickle=False)
        words = tuple(str(w) for w in archive["words"])
        vectors = np.asarray(archive["embeddings"], dtype=np.float32)
        model = str(archive["model"])
        missing = tuple(str(w) for w in archive.get("missing_words", np.array([], dtype=str)))
        return cls(words=words, vectors=vectors, model=model, missing_words=missing)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            path,
            words=np.array(self.words, dtype=str),
            embeddings=self.vectors.astype(np.float32, copy=False),
            model=np.array(self.model),
            missing_words=np.array(self.missing_words, dtype=str),
        )
