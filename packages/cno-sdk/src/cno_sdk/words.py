"""Word lists for starting codenames.game matches in tests and bots."""

from __future__ import annotations

# Minimal 25-word board used by integration tests and bot simulations.
TEST_BOARD_WORDS: tuple[str, ...] = (
    "HEAVEN",
    "BULB",
    "CHICK",
    "MOUNT",
    "OCEAN",
    "RIVER",
    "STONE",
    "CLOUD",
    "PIANO",
    "GUITAR",
    "MAPLE",
    "TIGER",
    "EAGLE",
    "CROWN",
    "SHIELD",
    "ARROW",
    "BREAD",
    "CLOCK",
    "DREAM",
    "FLAME",
    "GRASS",
    "HORSE",
    "IVORY",
    "JUMBO",
    "KNIFE",
)


def build_word_pack_entries(
    words: tuple[str, ...] | list[str] = TEST_BOARD_WORDS,
    *,
    pack_name: str = "codenames.en.clue",
    pack_size: int = 400,
    language: str = "en",
) -> list[dict[str, str | int]]:
    return [
        {
            "word": word.upper(),
            "packName": pack_name,
            "packSize": pack_size,
            "language": language,
        }
        for word in words
    ]
