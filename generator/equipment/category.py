import json
import re
from pathlib import Path

from ..discover import discover_json

CATEGORY_CLASSES = {
    "MistItemCategory",
    "MistItemCategory_C",
    "MistItemCategoryGroup",
    "MistItemCategoryGroup_C",
}

CATEGORY_GROUP_CLASSES = {
    "MistItemCategoryGroup",
    "MistItemCategoryGroup_C",
}


def _load_objects(path: Path) -> list[dict]:
    """Load category metadata JSON."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    if isinstance(raw, list):
        return [obj for obj in raw if isinstance(obj, dict)]

    return [raw] if isinstance(raw, dict) else []


def _superstruct_name(obj: dict) -> str | None:
    """Return the Unreal SuperStruct class name."""
    value = obj.get("SuperStruct", {}).get("ObjectName")

    if not isinstance(value, str):
        return None

    match = re.search(r"'([^']+)'", value)

    return match.group(1) if match else value


def _property_name(obj: dict) -> str | None:
    """Return Properties.Name."""
    properties = obj.get("Properties")

    if not isinstance(properties, dict):
        return None

    value = properties.get("Name")

    if isinstance(value, dict):
        value = value.get("LocalizedString") or value.get("SourceString")

    return value.strip() if isinstance(value, str) and value.strip() else None


def is_equipment_category_path(path: Path) -> bool:
    """Return whether path is Equipment category metadata."""
    parts = {part.lower() for part in path.parts}

    if not {"items", "categories", "equipment"} <= parts:
        return False

    return any(
        _superstruct_name(obj) in CATEGORY_CLASSES for obj in _load_objects(path)
    )


def is_equipment_item_path(path: Path) -> bool:
    """Return whether path is an Equipment item JSON."""
    parts = {part.lower() for part in path.parts}

    return {"items", "equipment"} <= parts and "categories" not in parts


def category_name_for_path(path: Path) -> str | None:
    """Return the category's display name."""
    if not is_equipment_category_path(path):
        return None

    return next(
        (name for obj in _load_objects(path) if (name := _property_name(obj))),
        None,
    )


def category_key_from_ref(value: object) -> str | None:
    """Extract an Unreal asset name from an object reference."""
    if not isinstance(value, dict):
        return None

    for key in ("ObjectPath", "AssetPathName", "ObjectName"):
        ref = value.get(key)

        if not isinstance(ref, str) or not ref:
            continue

        if ref.startswith("/Game/"):
            return ref.rsplit("/", 1)[-1].split(".", 1)[0]

        match = re.search(r"'([^']+)'", ref)

        if match:
            return match.group(1)

    return None


def normalize_category_key(value: str) -> str:
    """Normalize a category identifier for comparisons."""
    value = value.strip()

    if value.endswith("_C"):
        value = value[:-2]

    return re.sub(r"[^a-z0-9]", "", value.lower())


def category_name_for(
    properties: dict,
    category_index: dict[str, str],
) -> str | None:
    """Resolve an item's Category reference."""
    key = category_key_from_ref(properties.get("Category"))

    if not key:
        return None

    normalized = normalize_category_key(key)

    if title := category_index.get(normalized):
        return title

    return next(
        (
            title
            for candidate, title in sorted(
                category_index.items(),
                key=lambda item: -len(item[0]),
            )
            if normalized.startswith(candidate)
        ),
        None,
    )


def category_parent_key(path: Path) -> str | None:
    """Return the normalized Parent reference."""
    if not is_equipment_category_path(path):
        return None

    for obj in _load_objects(path):
        properties = obj.get("Properties")

        if not isinstance(properties, dict):
            continue

        if key := category_key_from_ref(properties.get("Parent")):
            return normalize_category_key(key)

    return None


def is_equipment_category_group(path: Path) -> bool:
    """Return whether path is a category group."""
    if not is_equipment_category_path(path):
        return False

    return any(
        _superstruct_name(obj) in CATEGORY_GROUP_CLASSES for obj in _load_objects(path)
    )


def category_slug(value: str) -> str:
    """Convert a category display name to a Markdown slug."""
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "category"


def _is_under(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _category_paths(assets_root: Path) -> list[Path]:
    """Return Equipment category metadata JSON paths."""
    root = (
        assets_root
        / "Bellwright"
        / "Content"
        / "Mist"
        / "Data"
        / "Items"
        / "Categories"
        / "Equipment"
    )

    if not root.exists():
        return []

    return sorted(
        (
            path
            for path in discover_json(assets_root)
            if _is_under(path, root) and is_equipment_category_path(path)
        ),
        key=lambda path: str(path).lower(),
    )


def build_category_index(
    assets_root: Path,
) -> dict[str, str]:
    """Build normalized category references to display names."""
    index: dict[str, str] = {}

    for path in _category_paths(assets_root):
        name = category_name_for_path(path)

        if not name:
            continue

        index[normalize_category_key(name)] = name
        index[normalize_category_key(path.stem)] = name

        for obj in _load_objects(path):
            object_name = obj.get("Name")

            if isinstance(object_name, str):
                index[normalize_category_key(object_name)] = name

    return index


def build_category_hierarchy(
    assets_root: Path,
) -> tuple[dict[str, set[str]], dict[str, str]]:
    """Build the Equipment hierarchy from Parent references."""
    paths = _category_paths(assets_root)

    titles = {"equipment": "Equipment"}

    for path in paths:
        if name := category_name_for_path(path):
            titles[normalize_category_key(name)] = name

    children = {key: set() for key in titles}

    for path in paths:
        title = category_name_for_path(path)

        if not title:
            continue

        child_key = normalize_category_key(title)

        if child_key == "equipment":
            continue

        parent_key = category_parent_key(path)

        if parent_key not in titles:
            continue

        children.setdefault(parent_key, set()).add(child_key)

    return children, titles


def category_row_scope(
    title: str,
    descendants: dict[str, set[str]],
    titles: dict[str, str],
) -> set[str]:
    """Return a category and all descendants."""
    start = normalize_category_key(title)
    scope: set[str] = set()
    stack = [start]

    while stack:
        current = stack.pop()

        if current in scope:
            continue

        scope.add(current)
        stack.extend(descendants.get(current, ()))

    return scope
