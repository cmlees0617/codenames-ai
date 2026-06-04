"""Generate GloVe embeddings for ``data/words.txt`` and write ``data/glove-wiki-gigaword-300.npz``."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from clue_eval.embeddings.store import (
    MODEL_NAME,
    VECTOR_SIZE,
    EmbeddingStore,
    default_embeddings_path,
    load_words_from_file,
)
from clue_eval.paths import package_data_dir


def _load_gensim_model():
    import gensim.downloader as api

    return api.load(MODEL_NAME)


def _lookup_vector(model, word: str) -> np.ndarray | None:
    """Resolve a GloVe vector; multi-word phrases use the mean of known tokens."""
    key = word.lower()
    if key in model:
        return np.asarray(model[key], dtype=np.float32)

    tokens = key.split()
    if len(tokens) < 2:
        return None

    token_vectors = [np.asarray(model[token], dtype=np.float32) for token in tokens if token in model]
    if not token_vectors:
        return None
    return np.mean(token_vectors, axis=0).astype(np.float32)


def build_store(
    words: list[str],
    *,
    model=None,
) -> EmbeddingStore:
    """Look up GloVe vectors for each word (lowercase key in the model)."""
    if model is None:
        model = _load_gensim_model()

    if getattr(model, "vector_size", None) not in (None, VECTOR_SIZE):
        raise ValueError(
            f"Expected {VECTOR_SIZE}-dimensional vectors, got {model.vector_size}"
        )

    found_words: list[str] = []
    rows: list[np.ndarray] = []
    missing: list[str] = []

    for word in words:
        vector = _lookup_vector(model, word)
        if vector is not None:
            found_words.append(word)
            rows.append(vector)
        else:
            missing.append(word)

    if not rows:
        raise ValueError("No words received embeddings; check words.txt and model.")

    return EmbeddingStore(
        words=tuple(found_words),
        vectors=np.vstack(rows),
        model=MODEL_NAME,
        missing_words=tuple(missing),
    )


def generate(
    *,
    words_path: Path | None = None,
    output_path: Path | None = None,
    verbose: bool = True,
) -> EmbeddingStore:
    words_file = words_path or (package_data_dir() / "words.txt")
    out_file = output_path or default_embeddings_path()

    words = load_words_from_file(words_file)
    if verbose:
        print(f"Loading {MODEL_NAME} via gensim...")
    store = build_store(words)
    store.save(out_file)

    if verbose:
        print(f"Words in {words_file.name}: {len(words)}")
        print(f"Embedded: {len(store.words)}")
        if store.missing_words:
            print(f"Missing ({len(store.missing_words)}): {', '.join(store.missing_words)}")
        print(f"Wrote {out_file} ({store.dimension}-d, {store.vectors.nbytes / 1e6:.2f} MB raw)")
    return store


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=f"Embed data/words.txt with GloVe ({MODEL_NAME}) and save to data/.",
    )
    parser.add_argument(
        "--words",
        type=Path,
        default=None,
        help="Word list file (default: package data/words.txt)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=f"Output .npz path (default: data/{default_embeddings_path().name})",
    )
    parser.add_argument("-q", "--quiet", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    generate(
        words_path=args.words,
        output_path=args.output,
        verbose=not args.quiet,
    )


if __name__ == "__main__":
    main()
