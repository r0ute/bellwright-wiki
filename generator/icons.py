from pathlib import Path

ICON_EXTENSIONS = {".webp"}


def build_icon_index(assets_root: Path) -> dict[str, Path]:
    """
    Build an index:

        icon filename stem -> actual icon path

    Example:
        T_ItemTypeArrows.webp
        -> "t_itemtypearrows": Path(...)
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
    Convert an Unreal/FModel AssetPathName/ObjectPath into
    the extracted filename stem.

    Examples:

        /Game/Mist/UI/Icons_new/ResourcesType/T_ItemTypeArrows.0
        -> T_ItemTypeArrows

        /Game/Mist/UI/Icons_new/ResourcesType/T_ItemTypeArrows
        -> T_ItemTypeArrows

        Texture2D'T_ItemTypeArrows'
        -> T_ItemTypeArrows
    """
    if not isinstance(asset_path_name, str) or not asset_path_name:
        return ""

    value = asset_path_name.strip()

    # Remove Unreal object wrapper:
    # Texture2D'Foo' -> Foo
    if "'" in value:
        match = value.rsplit("'", 2)
        if len(match) == 3 and match[1]:
            value = match[1]

    # Remove export/object instance suffix:
    # Foo.0 -> Foo
    value = value.split(".")[0]

    return Path(value).name


def find_icon(
    properties: dict,
    icon_index: dict[str, Path],
) -> Path | None:
    """
    Resolve Properties.Icon to an extracted .webp icon.

    FModel may expose the reference using either:
        ObjectPath
        AssetPathName
        ObjectName
    """
    icon = properties.get("Icon")

    if not isinstance(icon, dict):
        return None

    # Prefer the actual Unreal asset path.
    for key in ("ObjectPath", "AssetPathName", "ObjectName"):
        value = icon.get(key)

        if not isinstance(value, str) or not value:
            continue

        stem = asset_path_stem(value)

        if not stem:
            continue

        result = icon_index.get(stem.lower())

        if result:
            return result

    return None


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
