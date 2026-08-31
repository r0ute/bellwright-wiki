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

    if match:
        return match.group(1)

    return value


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

    if isinstance(value, str) and value.strip():
        return value.strip()

    return None


def _is_mist_category_class(object_name: str | None) -> bool:
    if not object_name:
        return False

    return object_name in {
        "MistItemCategory",
        "MistItemCategory_C",
        "MistItemCategoryGroup",
        "MistItemCategoryGroup_C",
    }


def is_equipment_category_path(path: Path) -> bool:
    """
    Return True for actual Equipment category metadata JSON.

    Category identity comes from the Unreal JSON metadata, not the
    filename. This means ClothingCategoryGroup.json correctly
    represents the category named "Clothing".
    """
    lower_parts = [part.lower() for part in path.parts]

    if not (
        "items" in lower_parts
        and "categories" in lower_parts
        and "equipment" in lower_parts
    ):
        return False

    for obj in _load_json_objects(path):
        object_name = _superstruct_object_name(obj)

        if _is_mist_category_class(object_name):
            return True

    return False


def is_equipment_item_path(path: Path) -> bool:
    """Return True for equipment item JSON outside Categories."""
    lower_parts = [part.lower() for part in path.parts]

    return (
        "items" in lower_parts
        and "equipment" in lower_parts
        and "categories" not in lower_parts
    )


def category_name_for_path(path: Path) -> str | None:
    """
    Return the canonical category name from Properties.Name.

    Examples:

        Equipment.json
            -> Equipment

        Ammo.json
            -> Ammo

        ClothingCategoryGroup.json
            -> Clothing
    """
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
    """
    Return True when the JSON represents a MistItemCategoryGroup.

    Note:
        ClothingCategoryGroup.json returns True here, but its canonical
        category name is still "Clothing", not "ClothingCategoryGroup".
    """
    if not is_equipment_category_path(path):
        return False

    for obj in _load_json_objects(path):
        object_name = _superstruct_object_name(obj)

        if object_name in {
            "MistItemCategoryGroup",
            "MistItemCategoryGroup_C",
        }:
            return True

    return False


def category_parent_key(path: Path) -> str | None:
    """
    Return the normalized key of Properties.Parent.

    Example:

        ClothingCategoryGroup.json
            Parent.ObjectName = BlueprintGeneratedClass'Equipment_C'

        -> "equipment"
    """
    if not is_equipment_category_path(path):
        return None

    for obj in _load_json_objects(path):
        properties = obj.get("Properties")

        if not isinstance(properties, dict):
            continue

        parent = properties.get("Parent")

        if not isinstance(parent, dict):
            continue

        for field in (
            "ObjectPath",
            "AssetPathName",
            "ObjectName",
        ):
            value = parent.get(field)

            if not isinstance(value, str) or not value:
                continue

            # /Game/.../Equipment.0
            if value.startswith("/Game/"):
                value = value.split("/")[-1]
                value = value.split(".")[0]

            # BlueprintGeneratedClass'Equipment_C'
            match = re.search(r"'([^']+)'", value)

            if match:
                value = match.group(1)

            return normalize_category_key(value)

    return None


def normalize_category_key(value: str) -> str:
    """
    Normalize Unreal category identifiers.

    Examples:

        Equipment_C             -> equipment
        ClothingCategoryGroup_C -> clothingcategorygroup
        Equipment               -> equipment
    """
    cleaned = value.strip()

    if cleaned.endswith("_C"):
        cleaned = cleaned[:-2]

    return re.sub(r"[^a-z0-9]", "", cleaned.lower())


def category_key_for_path(path: Path) -> str | None:
    """
    Return the canonical category key based on Properties.Name.

    This is intentionally NOT based on path.stem.
    """
    name = category_name_for_path(path)

    if not name:
        return None

    return normalize_category_key(name)
