import json
import re
from pathlib import Path


def _load_json_objects(path: Path) -> list[dict]:
    """Load a JSON file to a list of objects, handling single-object payloads."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []

    return raw if isinstance(raw, list) else ([raw] if isinstance(raw, dict) else [])


def _superstruct_object_name(obj: dict) -> str | None:
    """Read the Unreal class name behind a category metadata object.

    If the name is wrapped like "Class'Foo'" return the inner token (Foo).
    """
    if not isinstance(obj, dict):
        return None

    super_struct = obj.get("SuperStruct")
    if not isinstance(super_struct, dict):
        return None

    value = super_struct.get("ObjectName")
    if not isinstance(value, str):
        return None

    # Extract inner name from quotes if present: Class'Name' -> Name
    match = re.search(r"'([^']+)'", value)
    if match:
        return match.group(1)

    return value


def is_equipment_category_path(path: Path) -> bool:
    """Return True for category metadata files anywhere under Equipment."""
    lower_parts = [part.lower() for part in path.parts]
    if not (
        "items" in lower_parts
        and "categories" in lower_parts
        and "equipment" in lower_parts
    ):
        return False

    for obj in _load_json_objects(path):
        object_name = _superstruct_object_name(obj)
        if not object_name:
            continue
        # Accept both category objects and category-group wrapper objects
        # so group titles can be indexed and used as fallbacks for child
        # category references that don't have their own files.
        if re.match(r"^MistItemCategory(?:_C)?$", object_name) or re.match(r"^MistItemCategoryGroup(?:_C)?$", object_name):
            return True

    return False


def is_equipment_item_path(path: Path) -> bool:
    """Return True for real equipment item JSON under the Equipment tree."""
    lower_parts = [part.lower() for part in path.parts]
    return (
        "items" in lower_parts
        and "equipment" in lower_parts
        and "categories" not in lower_parts
    )


def category_name_for_path(path: Path) -> str | None:
    """Resolve the canonical category name from a file's metadata."""
    if not is_equipment_category_path(path):
        return None

    for obj in _load_json_objects(path):
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
def is_equipment_category_group(path: Path) -> bool:
    """Return True for category-group wrapper files (MistItemCategoryGroup)."""
    if not is_equipment_category_path(path):
        return False

    for obj in _load_json_objects(path):
        object_name = _superstruct_object_name(obj)
        if not object_name:
            continue
        if re.match(r"^MistItemCategoryGroup(?:_C)?$", object_name):
            return True

    return False
