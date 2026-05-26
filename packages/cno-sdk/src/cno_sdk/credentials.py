"""Generate vocalidio-style credentials matching the web client."""

from __future__ import annotations

import random
import string


_SYLLABLES = (
    "ba", "be", "bi", "bo", "bu", "ca", "ce", "ci", "co", "cu",
    "da", "de", "di", "do", "du", "fa", "fe", "fi", "fo", "fu",
    "ga", "ge", "gi", "go", "gu", "ha", "he", "hi", "ho", "hu",
    "ja", "je", "ji", "jo", "ju", "ka", "ke", "ki", "ko", "ku",
    "la", "le", "li", "lo", "lu", "ma", "me", "mi", "mo", "mu",
    "na", "ne", "ni", "no", "nu", "pa", "pe", "pi", "po", "pu",
    "ra", "re", "ri", "ro", "ru", "sa", "se", "si", "so", "su",
    "ta", "te", "ti", "to", "tu", "va", "ve", "vi", "vo", "vu",
    "wa", "we", "wi", "wo", "wu", "ya", "ye", "yi", "yo", "yu",
    "za", "ze", "zi", "zo", "zu",
)


def _random_token(length: int) -> str:
    parts: list[str] = []
    while sum(len(p) for p in parts) < length:
        parts.append(random.choice(_SYLLABLES))
    token = "".join(parts)
    if len(token) > length:
        token = token[:length]
    return token


def generate_credentials() -> str:
    """Return a hyphenated token like ``rosilitu-hasumotu-luhoniba``."""
    return "-".join(_random_token(random.randint(6, 9)) for _ in range(3))


def generate_player_id() -> str:
    """BGIO player IDs are numeric strings assigned by the server."""
    return str(random.randint(0, 63))
