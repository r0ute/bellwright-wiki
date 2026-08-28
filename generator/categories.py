from pathlib import Path


def is_weapon_category_path(path: Path) -> bool:
    """Return True for category metadata files under Weapon categories."""
    lower_parts = [part.lower() for part in path.parts]
    return "categories" in lower_parts and "weapons" in lower_parts


def category_from_path(path: Path) -> str | None:
    """
    Determine the asset category from its directory path.
    Category metadata files are excluded so only real item assets are counted.
    """
    lower_parts = [part.lower() for part in path.parts]

    if is_weapon_category_path(path):
        return None

    if "weapons" in lower_parts[:-1]:
        return "weapons"

    return None