import json
from collections.abc import Iterator
from pathlib import Path

from ..discover import discover_json
from .category import is_equipment_item_path


def load_objects(path: Path) -> list[dict]:
    """Load FModel JSON as a list of objects."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    return raw if isinstance(raw, list) else [raw]


def find_cdo(objects: list[dict]) -> dict | None:
    """Return the first object containing Properties."""
    return next(
        (
            obj
            for obj in objects
            if isinstance(obj, dict) and isinstance(obj.get("Properties"), dict)
        ),
        None,
    )


def load_properties(path: Path) -> dict:
    """Return the CDO Properties."""
    cdo = find_cdo(load_objects(path))

    if not cdo:
        return {}

    properties = cdo["Properties"]

    return properties if isinstance(properties, dict) else {}


def discover_items(assets_root: Path) -> Iterator[Path]:
    """Yield equipment item JSON paths."""
    return (path for path in discover_json(assets_root) if is_equipment_item_path(path))
