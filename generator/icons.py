from pathlib import Path


ICON_EXTENSIONS = ".webp"


def build_icon_index(assets_root: Path) -> dict[str, Path]:
    """
    Build:
        filename stem -> actual icon path
    """
    index: dict[str, Path] = {}

    for path in assets_root.rglob("*"):
        if not path.is_file():
            continue

        if path.suffix.lower() not in ICON_EXTENSIONS:
            continue

        index.setdefault(path.stem.lower(), path)

    return index


def asset_path_stem(asset_path_name: str) -> str:
    """
    Convert an Unreal/FModel AssetPathName into a filename stem.
    """
    if not asset_path_name:
        return ""

    value = asset_path_name.split(".")[0]

    return Path(value).name


def find_icon(
    properties: dict,
    icon_index: dict[str, Path],
) -> Path | None:
    """Resolve Properties.Icon to an actual extracted image."""
    icon = properties.get("Icon")

    if not isinstance(icon, dict):
        return None

    asset_path = icon.get("AssetPathName", "")

    if not isinstance(asset_path, str):
        return None

    stem = asset_path_stem(asset_path)

    if not stem:
        return None

    return icon_index.get(stem.lower())


def copy_icon(
    icon: Path,
    output_dir: Path,
) -> Path:
    """
    Copy an icon into the generated documentation assets.

    Returns the destination path.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    destination = output_dir / icon.name

    if not destination.exists() or destination.stat().st_size != icon.stat().st_size:
        destination.write_bytes(icon.read_bytes())

    return destination
