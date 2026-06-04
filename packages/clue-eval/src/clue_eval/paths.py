"""Filesystem paths for packaged evaluation data."""

from __future__ import annotations

from pathlib import Path


def package_data_dir() -> Path:
    """Directory containing ``test_boards.json`` and other fixture data."""
    return Path(__file__).resolve().parents[2] / "data"


def default_test_boards_path() -> Path:
    return package_data_dir() / "test_boards.json"
