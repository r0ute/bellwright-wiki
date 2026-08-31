import json
from pathlib import Path

from ..discover import discover_json
from . import category


def find_cdo(objects: list) -> dict | None:
    return next(
        (
            obj
            for obj in objects
            if isinstance(obj, dict) and isinstance(obj.get("Properties"), dict)
        ),
        None,
    )


def load_objects(path: Path) -> list:
    """Load FModel JSON as a list of objects."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []

    return raw if isinstance(raw, list) else [raw]


def load_properties(path: Path) -> dict:
    """Return the Properties object from the CDO."""
    objects = load_objects(path)
    cdo = find_cdo(objects)

    if not cdo:
        return {}

    properties = cdo.get("Properties")

    return properties if isinstance(properties, dict) else {}


def build_category_index(assets_root: Path) -> dict[str, str]:
    """
    Build:

        normalized category reference -> display name
    """
    category_index: dict[str, str] = {}

    for path in discover_json(assets_root):
        if not category.is_equipment_category_path(path):
            continue

        objects = load_objects(path)

        if not objects:
            continue

        name = category.category_name_for_path(path)

        if not name:
            continue

        category_index[category.normalize_category_key(name)] = name

        category_index[category.normalize_category_key(path.stem)] = name

        for obj in objects:
            if not isinstance(obj, dict):
                continue

            object_name = obj.get("Name")

            if isinstance(object_name, str):
                category_index[category.normalize_category_key(object_name)] = name

    return category_index


def _category_paths(assets_root: Path) -> list[Path]:
    """Return every category metadata JSON under Equipment."""
    category_root = (
        assets_root
        / "Bellwright"
        / "Content"
        / "Mist"
        / "Data"
        / "Items"
        / "Categories"
        / "Equipment"
    )

    if not category_root.exists():
        return []

    paths = [
        path
        for path in discover_json(assets_root)
        if _is_under(path, category_root) and category.is_equipment_category_path(path)
    ]

    return sorted(
        paths,
        key=lambda path: str(path).lower(),
    )


def build_category_hierarchy(
    assets_root: Path,
) -> tuple[dict[str, set[str]], dict[str, str]]:
    """
    Build the real Equipment hierarchy from Parent references.

    Equipment.json is always the root.
    """
    category_paths = _category_paths(assets_root)

    titles: dict[str, str] = {
        "equipment": "Equipment",
    }

    for path in category_paths:
        title = category.category_name_for_path(path)

        if not title:
            continue

        key = category.normalize_category_key(title)

        if key:
            titles[key] = title

    children: dict[str, set[str]] = {key: set() for key in titles}

    for path in category_paths:
        title = category.category_name_for_path(path)

        if not title:
            continue

        child_key = category.normalize_category_key(title)

        if child_key == "equipment":
            continue

        parent_key = category.category_parent_key(path)

        if not parent_key:
            continue

        parent_key = category.normalize_category_key(parent_key)

        if parent_key in titles:
            children.setdefault(parent_key, set()).add(child_key)

    return children, titles


def _is_under(path: Path, root: Path) -> bool:
    """Python-version-safe Path.is_relative_to()."""
    try:
        return path.is_relative_to(root)
    except AttributeError:
        try:
            path.relative_to(root)
            return True
        except ValueError:
            return False
