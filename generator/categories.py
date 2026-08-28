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


def category_from_path(path: Path) -> str | None:
    """Return a generic equipment category key for equipment assets."""
    if is_equipment_item_path(path):
        return "equipment-item"

    if is_equipment_category_path(path):
        return "equipment-category"

    return None