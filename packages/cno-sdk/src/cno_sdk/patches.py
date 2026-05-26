"""Apply RFC 6902 JSON patches to boardgame.io state."""

from __future__ import annotations

import copy
from typing import Any


def _path_parts(path: str) -> list[str]:
    if not path or path == "/":
        return []
    return [part.replace("~1", "/").replace("~0", "~") for part in path.split("/")[1:]]


def _resolve_parent(root: Any, parts: list[str]) -> tuple[Any, str]:
    current = root
    for part in parts[:-1]:
        current = current[int(part)] if isinstance(current, list) else current[part]
    last = parts[-1]
    return current, last


def apply_json_patches(state: dict[str, Any], patches: list[dict[str, Any]]) -> dict[str, Any]:
    """Apply a list of JSON Patch operations to a deep-copied state dict."""
    updated = copy.deepcopy(state)
    for patch in patches:
        op = patch["op"]
        parts = _path_parts(patch["path"])
        value = patch.get("value")

        if op == "replace":
            parent, key = _resolve_parent(updated, parts)
            if isinstance(parent, list):
                parent[int(key)] = copy.deepcopy(value)
            else:
                parent[key] = copy.deepcopy(value)
        elif op == "add":
            parent, key = _resolve_parent(updated, parts)
            if isinstance(parent, list):
                index = int(key) if key != "-" else len(parent)
                parent.insert(index, copy.deepcopy(value))
            else:
                parent[key] = copy.deepcopy(value)
        elif op == "remove":
            parent, key = _resolve_parent(updated, parts)
            if isinstance(parent, list):
                index = int(key)
                if 0 <= index < len(parent):
                    del parent[index]
            elif key in parent:
                del parent[key]
        else:
            raise ValueError(f"Unsupported JSON patch op: {op}")

    return updated
