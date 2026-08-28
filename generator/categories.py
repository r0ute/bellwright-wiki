
from pathlib import Path


def category_from_path(path: Path) -> str | None:
    """
    Determine the asset category from its directory path.
    """
    for part in path.parts[:-1]:
        name = part.lower()

        if name == "weapons":
            return "weapons"

    return None