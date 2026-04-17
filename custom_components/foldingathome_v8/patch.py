"""Helpers for applying FAH websocket state updates."""

from __future__ import annotations

from collections.abc import MutableMapping, MutableSequence
from typing import Any


def normalize_key(value: Any) -> Any:
    """Normalize websocket keys for Python access."""
    if isinstance(value, str):
        return value.replace("-", "_")
    return value


def normalize_object(value: Any) -> Any:
    """Recursively normalize websocket payload data."""
    if isinstance(value, dict):
        return {
            normalize_key(key): normalize_object(item) for key, item in value.items()
        }
    if isinstance(value, list):
        return [normalize_object(item) for item in value]
    return value


def apply_update(target: dict[str, Any], update: list[Any]) -> dict[str, Any]:
    """Apply a FAH websocket patch update to a snapshot in place."""
    if not update:
        return target

    path = [normalize_key(part) for part in update[:-1]]
    value = normalize_object(update[-1])
    _apply(target, path, value)
    return target


def _apply(container: Any, path: list[Any], value: Any) -> None:
    if not path:
        raise ValueError("Patch path cannot be empty")

    current = path[0]

    if len(path) == 1:
        _apply_terminal(container, current, value)
        return

    next_key = path[1]
    next_container_type = list if isinstance(next_key, int) else dict

    if isinstance(container, MutableMapping):
        child = container.get(current)
        if not isinstance(child, next_container_type):
            child = [] if next_container_type is list else {}
            container[current] = child
        _apply(child, path[1:], value)
        return

    if isinstance(container, MutableSequence):
        if not isinstance(current, int) or current < 0:
            raise ValueError(f"Invalid list index in patch path: {current!r}")
        _ensure_list_size(container, current)
        child = container[current]
        if not isinstance(child, next_container_type):
            child = [] if next_container_type is list else {}
            container[current] = child
        _apply(child, path[1:], value)
        return

    raise TypeError(f"Unsupported container type: {type(container)!r}")


def _apply_terminal(container: Any, key: Any, value: Any) -> None:
    if isinstance(container, MutableMapping):
        if value is None:
            container.pop(key, None)
        else:
            container[key] = value
        return

    if isinstance(container, MutableSequence):
        if not isinstance(key, int):
            raise ValueError(f"Invalid list index in patch path: {key!r}")

        if key == -1:
            if value is not None:
                container.append(value)
            return

        if key == -2:
            if value is None:
                return
            if not isinstance(value, list):
                raise ValueError("Patch concatenate value must be a list")
            container.extend(value)
            return

        if key < 0:
            raise ValueError(f"Unsupported list operation index: {key!r}")

        _ensure_list_size(container, key)
        if value is None:
            container.pop(key)
        else:
            container[key] = value
        return

    raise TypeError(f"Unsupported container type: {type(container)!r}")


def _ensure_list_size(container: MutableSequence[Any], index: int) -> None:
    while len(container) <= index:
        container.append(None)

