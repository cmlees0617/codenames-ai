"""GameBackend is defined for future backends; no implementation yet."""

from game_core.backends import GameBackend


def test_game_backend_is_runtime_checkable_protocol() -> None:
    assert isinstance(GameBackend, type)
