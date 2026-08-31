from collections.abc import Iterator
from pathlib import Path

JSON_EXTENSIONS = {".json"}


def discover_json(assets_root: Path) -> Iterator[Path]:
    """
    Recursively yield JSON files under the assets directory.

    Matching is case-insensitive and limited to JSON_EXTENSIONS.
    """
    for path in assets_root.rglob("*"):
        if path.is_file() and path.suffix.lower() in JSON_EXTENSIONS:
            yield path
