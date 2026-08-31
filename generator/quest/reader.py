"""Read exported Unreal JSON objects."""

import json
from pathlib import Path


def read_objects(path: Path) -> list[dict]:
    """Read and normalize objects from an exported JSON file."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
    ):
        return []

    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]

    if isinstance(value, dict):
        objects = value.get("Objects")

        if isinstance(objects, list):
            return [item for item in objects if isinstance(item, dict)]

        return [value]

    return []
