from pathlib import Path
from typing import Iterator

JSON_EXTENSIONS = {".json"}
ICON_EXTENSIONS = {".webp"}


def discover_json(assets_root: Path) -> Iterator[Path]:
    """Recursively yield every JSON file under the assets directory."""
    yield from (
        path
        for path in assets_root.rglob("*")
        if path.is_file() and path.suffix.lower() in JSON_EXTENSIONS
    )


def discover_icons(assets_root: Path) -> Iterator[Path]:
    """Recursively yield every supported icon/image asset."""
    yield from (
        path
        for path in assets_root.rglob("*")
        if path.is_file() and path.suffix.lower() in ICON_EXTENSIONS
    )
