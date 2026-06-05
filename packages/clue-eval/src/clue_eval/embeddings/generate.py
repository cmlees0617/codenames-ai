"""Generate GloVe embeddings for ``data/words.txt`` and write ``data/glove-wiki-gigaword-300.npz``."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from clue_eval.embeddings.glove import load_gensim_model, lookup_vector
from clue_eval.embeddings.store import (
    MODEL_NAME,
    VECTOR_SIZE,
    EmbeddingStore,
    default_embeddings_path,
    load_words_from_file,
)
from clue_eval.paths import package_data_dir


def build_store(
    words: list[str],
    *,
    model=None,
) -> EmbeddingStore:
    """Look up GloVe vectors for each word (lowercase key in the model)."""
    if model is None:
        model = load_gensim_model()

    if getattr(model, "vector_size", None) not in (None, VECTOR_SIZE):
        raise ValueError(
            f"Expected {VECTOR_SIZE}-dimensional vectors, got {model.vector_size}"
        )

    found_words: list[str] = []
    rows: list[np.ndarray] = []
    missing: list[str] = []

    for word in words:
        vector = lookup_vector(model, word)
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
