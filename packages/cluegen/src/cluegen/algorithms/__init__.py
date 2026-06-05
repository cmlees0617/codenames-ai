from cluegen.algorithms.clue import CluegenClueAlgorithm
from cluegen.algorithms.scripted import ScriptedClueAlgorithm, ScriptedGuessAlgorithm

__all__ = [
    "CluegenClueAlgorithm",
    "EmbeddingGuessAlgorithm",
    "RandomGuessAlgorithm",
    "ScriptedClueAlgorithm",
    "ScriptedGuessAlgorithm",
]


def __getattr__(name: str):
    if name == "EmbeddingGuessAlgorithm":
        from cluegen.algorithms.guess import EmbeddingGuessAlgorithm

        return EmbeddingGuessAlgorithm
    if name == "RandomGuessAlgorithm":
        from cluegen.algorithms.guess import RandomGuessAlgorithm

        return RandomGuessAlgorithm
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
