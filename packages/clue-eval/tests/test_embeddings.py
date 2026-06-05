import numpy as np
import pytest
from clue_eval.embeddings.generate import build_store
from clue_eval.embeddings.store import (
    MODEL_NAME,
    VECTOR_SIZE,
    EmbeddingStore,
    default_embeddings_path,
    load_words_from_file,
)
from clue_eval.paths import package_data_dir


def test_words_file_has_expected_count():
    words = load_words_from_file(package_data_dir() / "words.txt")
    assert len(words) == 400


@pytest.mark.skipif(
    not default_embeddings_path().exists(),
    reason="Run: uv run --extra embeddings clue-eval-embed",
)
def test_packaged_embeddings_load():
    store = EmbeddingStore.load()
    assert store.model == MODEL_NAME
    assert store.dimension == VECTOR_SIZE
    assert store.vectors.shape[0] == len(store.words)
    assert store.vectors.dtype == np.float32
    assert len(store.missing_words) == 0


def test_build_store_from_subset():
    pytest.importorskip("gensim")
    import gensim.downloader as api

    model = api.load(MODEL_NAME)
    store = build_store(["APPLE", "RIVER"], model=model)
    assert store.words == ("APPLE", "RIVER")
    assert store.vectors.shape == (2, VECTOR_SIZE)
