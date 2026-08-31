import json
import re
from pathlib import Path


def _load_json_objects(path: Path) -> list[dict]:
    """Load a JSON file into a list of objects."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    if isinstance(raw, list):
        return [obj for obj in raw if isinstance(obj, dict)]

    if isinstance(raw, dict):
        return [raw]

    return []


def _superstruct_object_name(obj: dict) -> str | None:
    """Return the Unreal SuperStruct class name."""
    if not isinstance(obj, dict):
        return None

    super_struct = obj.get("SuperStruct")

    if not isinstance(super_struct, dict):
        return None

    value = super_struct.get("ObjectName")

    if not isinstance(value, str):
        return None

    match = re.search(r"'([^']+)'", value)

    return match.group(1) if match else value


def _property_name(obj: dict) -> str | None:
    """Return Properties.Name's localized/source string."""
    properties = obj.get("Properties")

    if not isinstance(properties, dict):
        return None

    name = properties.get("Name")

    if isinstance(name, dict):
        value = name.get("LocalizedString") or name.get("SourceString")
    else:
        value = name

    return value.strip() if isinstance(value, str) and value.strip() else None


def _is_mist_category_class(object_name: str | None) -> bool:
    return object_name in {
        "MistItemCategory",
        "MistItemCategory_C",
        "MistItemCategoryGroup",
        "MistItemCategoryGroup_C",
    }


def is_equipment_category_path(path: Path) -> bool:
    """
    Return True for actual Equipment category metadata JSON.

    Category identity comes from Unreal metadata rather than the filename.
    """
    lower_parts = [part.lower() for part in path.parts]

    if not {
        "items",
        "categories",
        "equipment",
    }.issubset(lower_parts):
        return False

    return any(
        _is_mist_category_class(_superstruct_object_name(obj))
        for obj in _load_json_objects(path)
    )


def is_equipment_item_path(path: Path) -> bool:
    """Return True for equipment item JSON outside Categories."""
    lower_parts = [part.lower() for part in path.parts]

    return (
        "items" in lower_parts
        and "equipment" in lower_parts
        and "categories" not in lower_parts
    )


def category_name_for_path(path: Path) -> str | None:
    """Return the canonical category name from Properties.Name."""
    if not is_equipment_category_path(path):
        return None

    for obj in _load_json_objects(path):
        name = _property_name(obj)

        if name:
            return name

    return None


def category_from_path(path: Path) -> str | None:
    """Return the broad type of an Equipment asset."""
    if is_equipment_item_path(path):
        return "equipment-item"

    if is_equipment_category_path(path):
        return "equipment-category"

    return None


def is_equipment_category_group(path: Path) -> bool:
    """Return True when the JSON represents a MistItemCategoryGroup."""
    if not is_equipment_category_path(path):
        return False

    return any(
        _superstruct_object_name(obj)
        in {
            "MistItemCategoryGroup",
            "MistItemCategoryGroup_C",
        }
        for obj in _load_json_objects(path)
    )


def category_key_from_ref(value: object) -> str | None:
    """Extract an Unreal asset/class name from an object reference."""
    if not isinstance(value, dict):
        return None

    for key in ("ObjectPath", "AssetPathName", "ObjectName"):
        ref = value.get(key)

        if not isinstance(ref, str) or not ref:
            continue

        if ref.startswith("/Game/"):
            return ref.split("/")[-1].split(".")[0]

        match = re.search(r"'([^']+)'", ref)

        if match:
            return match.group(1)

    return None


def category_name_for(
    properties: dict,
    category_index: dict[str, str],
) -> str | None:
    """Resolve an item's Category reference to its display name."""
    key = category_key_from_ref(properties.get("Category"))

    if not key:
        return None

    normalized = normalize_category_key(key)

    if title := category_index.get(normalized):
        return title

    for candidate_key, candidate_title in sorted(
        category_index.items(),
        key=lambda item: -len(item[0]),
    ):
        if normalized.startswith(candidate_key):
            return candidate_title

    return None


def category_parent_key(path: Path) -> str | None:
    """Return the normalized key of Properties.Parent."""
    if not is_equipment_category_path(path):
        return None

    for obj in _load_json_objects(path):
        properties = obj.get("Properties")

        if not isinstance(properties, dict):
            continue

        parent = properties.get("Parent")

        if not isinstance(parent, dict):
            continue

        if key := category_key_from_ref(parent):
            return normalize_category_key(key)

    return None


def normalize_category_key(value: str) -> str:
    """Normalize an Unreal category identifier."""
    cleaned = value.strip()

    if cleaned.endswith("_C"):
        cleaned = cleaned[:-2]

    return re.sub(r"[^a-z0-9]", "", cleaned.lower())


def category_key_for_path(path: Path) -> str | None:
    """Return the canonical category key from Properties.Name."""
    name = category_name_for_path(path)

    return normalize_category_key(name) if name else None


def category_slug(value: str) -> str:
    """Convert a category display name to a Markdown filename slug."""
    slug = re.sub(
        r"[^a-z0-9]+",
        "-",
        value.lower(),
    ).strip("-")

    return slug or "category"


def category_row_scope(
    title: str,
    descendants: dict[str, set[str]],
    titles: dict[str, str],
) -> set[str]:
    """Return the category plus all descendants."""
    start = normalize_category_key(title)

    scope: set[str] = set()
    stack = [start]

    while stack:
        current = stack.pop()

        if current in scope:
            continue

        scope.add(current)
        stack.extend(
            sorted(
                descendants.get(current, set()),
                key=str.lower,
                reverse=True,
            )
        )

    return scope
