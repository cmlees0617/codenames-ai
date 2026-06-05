"""Resolve spymaster model names for benchmark output files."""

from __future__ import annotations

import re

from game_core.algorithms import ClueAlgorithm, IdentifiableClueAlgorithm


def resolve_spymaster_name(algorithm: ClueAlgorithm) -> str:
    """
    Return a filesystem-safe identifier for ``algorithm``.

    Uses ``algorithm.name`` when the implementation exposes
    :class:`~game_core.algorithms.IdentifiableClueAlgorithm`; otherwise the class name.
    """
    if isinstance(algorithm, IdentifiableClueAlgorithm):
        return sanitize_model_filename(algorithm.name)
    explicit = getattr(algorithm, "name", None)
    if isinstance(explicit, str) and explicit.strip():
        return sanitize_model_filename(explicit)
    return sanitize_model_filename(type(algorithm).__name__)


def sanitize_model_filename(name: str) -> str:
    """Collapse unsafe characters for JSON result filenames."""
    cleaned = re.sub(r"[^\w.\-]+", "_", name.strip())
    return cleaned or "spymaster"
