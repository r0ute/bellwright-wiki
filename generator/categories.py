import json
from pathlib import Path


def is_equipment_category_path(path: Path) -> bool:
    """Return True for category metadata files anywhere under Equipment."""
    lower_parts = [part.lower() for part in path.parts]
    return (
        "items" in lower_parts
        and "categories" in lower_parts
        and "equipment" in lower_parts
    )


def is_equipment_item_path(path: Path) -> bool:
    """Return True for real equipment item JSON under the Equipment tree."""
    lower_parts = [part.lower() for part in path.parts]
    return (
        "items" in lower_parts
        and "equipment" in lower_parts
        and "categories" not in lower_parts
    )


def is_equipment_category_group(path: Path) -> bool:
    """Return True for wrapper category-group files that should not be page roots."""
    if not is_equipment_category_path(path):
        return False

    return path.stem.endswith("CategoryGroup")


def category_name_for_path(path: Path) -> str | None:
    """Resolve the canonical category name from a file's metadata."""
    if not is_equipment_category_path(path):
        return None

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

    objects = raw if isinstance(raw, list) else [raw]
    for obj in objects:
        if not isinstance(obj, dict):
            continue
        props = obj.get("Properties")
        if not isinstance(props, dict):
            continue
        name = props.get("Name")
        if isinstance(name, dict):
            value = name.get("LocalizedString") or name.get("SourceString")
        else:
            value = name

        if isinstance(value, str) and value:
            return value

    return None


def category_from_path(path: Path) -> str | None:
    """Return a generic equipment category key for equipment assets."""
    if is_equipment_item_path(path):
        return "equipment-item"

    if is_equipment_category_path(path):
        return "equipment-category"

    return None