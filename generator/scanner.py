import json
import re
from pathlib import Path

from generator.categories import is_equipment_category_path
from generator.discover import discover_json
from generator.icons import copy_icon, find_icon

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
DOCS = ROOT / "docs"
ICON_OUT = DOCS / "assets" / "icons"


def find_cdo(objects: list) -> dict | None:
    return next(
        (
            obj
            for obj in objects
            if isinstance(obj, dict) and isinstance(obj.get("Properties"), dict)
        ),
        None,
    )


def asset_name(path: Path, objects: list) -> str:
    cdo = find_cdo(objects)

    if not cdo:
        return path.stem

    name = cdo["Properties"].get("Name")

    if isinstance(name, dict):
        return name.get("LocalizedString") or name.get("SourceString") or path.stem

    if isinstance(name, str) and name:
        return name

    return path.stem


def normalize_category_key(value: str) -> str:
    cleaned = value.strip()

    if cleaned.endswith("_C"):
        cleaned = cleaned[:-2]

    return re.sub(r"[^a-z0-9]", "", cleaned.lower())


def category_key_from_ref(value: object) -> str | None:
    """
    Extract the Unreal asset/class name from an object reference.

    Examples:

        {
            "ObjectName": "BlueprintGeneratedClass'Equipment_C'",
            "ObjectPath": "/Game/.../Equipment.0"
        }

        -> Equipment_C

    """
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


def load_objects(path: Path) -> list:
    """Load FModel JSON as a list of objects."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []

    return raw if isinstance(raw, list) else [raw]


def load_properties(path: Path) -> dict:
    """Return the Properties object from the CDO."""
    objects = load_objects(path)
    cdo = find_cdo(objects)

    if not cdo:
        return {}

    properties = cdo.get("Properties")

    return properties if isinstance(properties, dict) else {}


def build_category_index(assets_root: Path) -> dict[str, str]:
    """
    Build:

        normalized category reference -> display name

    Example:

        equipment -> Equipment
        ammo -> Ammo
        armors -> Armors
        clothingcategorygroup -> Clothing
        clothing -> Clothing
    """
    category_index: dict[str, str] = {}

    for path in discover_json(assets_root):
        if not is_equipment_category_path(path):
            continue

        objects = load_objects(path)

        if not objects:
            continue

        name = asset_name(path, objects)

        category_index[normalize_category_key(name)] = name
        category_index[normalize_category_key(path.stem)] = name

        # Also index the Blueprint class name where available.
        for obj in objects:
            if not isinstance(obj, dict):
                continue

            object_name = obj.get("Name")

            if isinstance(object_name, str):
                category_index[normalize_category_key(object_name)] = name

    return category_index


def category_name_for(
    properties: dict,
    category_index: dict[str, str],
) -> str | None:
    """
    Resolve an item's Category reference to the canonical
    category display name.
    """
    category_ref = properties.get("Category")
    key = category_key_from_ref(category_ref)

    if not key:
        return None

    normalized = normalize_category_key(key)

    title = category_index.get(normalized)

    if title:
        return title

    # Only use prefix matching as a final fallback.
    for candidate_key, candidate_title in sorted(
        category_index.items(),
        key=lambda item: -len(item[0]),
    ):
        if normalized.startswith(candidate_key):
            return candidate_title

    return None


def generate_equipment_item(
    path: Path,
    objects: list,
    icon_index: dict[str, Path],
    category_index: dict[str, str],
) -> dict:
    cdo = find_cdo(objects)

    if not cdo:
        raise ValueError(f"No CDO found: {path}")

    properties = cdo.get("Properties", {})

    if not isinstance(properties, dict):
        properties = {}

    name = asset_name(path, objects)

    category_name = category_name_for(properties, category_index) or "Uncategorized"

    icon = find_icon(properties, icon_index)

    icon_md = ""

    if icon:
        destination = copy_icon(icon, ICON_OUT)

        icon_md = f'<img src="assets/icons/{destination.name}" alt="{name}" width="48">'

    context = {
        "name": name,
        "icon": icon_md,
        "path": path,
    }

    return {
        "properties": properties,
        "context": context,
        "Category": category_name,
    }


def category_slug(value: str) -> str:
    """
    Convert a category display name to the Markdown filename slug.

    ClothingCategoryGroup -> never reaches this function as the title;
    the JSON metadata says Name = Clothing.

    Clothing -> clothing
    Ammo -> ammo
    Armors -> armors
    """
    slug = re.sub(
        r"[^a-z0-9]+",
        "-",
        value.lower(),
    ).strip("-")

    return slug or "category"


def _is_under(path: Path, root: Path) -> bool:
    """Python-version-safe Path.is_relative_to()."""
    try:
        return path.is_relative_to(root)
    except AttributeError:
        try:
            root.relative_to(path)
            return False
        except ValueError:
            return root in path.parents or path == root


def _category_parent_key(path: Path) -> str | None:
    """
    Read the category's actual Parent reference.

    This is the important part: Equipment.json does NOT contain
    a Children property in the supplied FModel extraction.
    """
    properties = load_properties(path)

    parent = properties.get("Parent")

    return category_key_from_ref(parent)


def _category_paths(assets_root: Path) -> list[Path]:
    """Return every category metadata JSON under Equipment."""
    category_root = (
        assets_root
        / "Bellwright"
        / "Content"
        / "Mist"
        / "Data"
        / "Items"
        / "Categories"
        / "Equipment"
    )

    if not category_root.exists():
        return []

    paths = []

    for path in discover_json(assets_root):
        if not _is_under(path, category_root):
            continue

        if is_equipment_category_path(path):
            paths.append(path)

    return sorted(
        paths,
        key=lambda path: str(path).lower(),
    )


def equipment_category_paths(assets_root: Path) -> list[Path]:
    """
    Return the actual top-level Equipment category groups.

    Equipment.json is the root and maps to index.md.

    Its direct children are determined from each category's Parent
    reference, NOT from Equipment.json.Children.

    Expected result:

        Ammo/Ammo.json
        Armors/Armors.json
        Clothing/ClothingCategoryGroup.json
        Gear/Gear.json
        Tools/Tools.json
        Weapons/Weapons.json
    """
    category_root = (
        assets_root
        / "Bellwright"
        / "Content"
        / "Mist"
        / "Data"
        / "Items"
        / "Categories"
        / "Equipment"
    )

    if not category_root.exists():
        return []

    equipment_json = category_root / "Equipment.json"

    if not equipment_json.exists():
        return []

    equipment_key = "equipment"

    paths: list[Path] = []
    seen: set[str] = set()

    for path in _category_paths(assets_root):
        # Equipment.json itself is the root -> index.md.
        if path == equipment_json:
            continue

        parent_key = _category_parent_key(path)

        if not parent_key:
            continue

        if normalize_category_key(parent_key) != equipment_key:
            continue

        objects = load_objects(path)

        if not objects:
            continue

        title = asset_name(path, objects)
        key = normalize_category_key(title)

        if key in seen:
            continue

        seen.add(key)
        paths.append(path)

    return sorted(
        paths,
        key=lambda path: asset_name(
            path,
            load_objects(path),
        ).lower(),
    )


def build_category_hierarchy(
    assets_root: Path,
) -> tuple[dict[str, set[str]], dict[str, str]]:
    """
    Build the real Equipment hierarchy from Parent references.

    Equipment.json is always the root.

    Direct children are categories whose Parent is Equipment_C.

    Any deeper category is assigned to the category referenced by
    its Parent.

    This does not depend on a nonexistent Equipment.Children property.
    """
    category_paths = _category_paths(assets_root)

    titles: dict[str, str] = {
        "equipment": "Equipment",
    }

    path_by_key: dict[str, Path] = {}

    # First collect canonical names and paths.
    for path in category_paths:
        objects = load_objects(path)

        if not objects:
            continue

        title = asset_name(path, objects)
        key = normalize_category_key(title)

        if not key:
            continue

        titles[key] = title
        path_by_key[key] = path

        # Also allow references using the filename/class name.
        path_by_key.setdefault(
            normalize_category_key(path.stem),
            path,
        )

    children: dict[str, set[str]] = {key: set() for key in titles}

    children.setdefault("equipment", set())

    # Assign each category to its actual Parent.
    for path in category_paths:
        objects = load_objects(path)

        if not objects:
            continue

        title = asset_name(path, objects)
        child_key = normalize_category_key(title)

        if child_key == "equipment":
            continue

        parent_key = _category_parent_key(path)

        if not parent_key:
            continue

        parent_key = normalize_category_key(parent_key)

        # Resolve parent references such as:
        # Equipment_C -> equipment
        parent_title = titles.get(parent_key)

        if parent_title:
            parent_key = normalize_category_key(parent_title)

        # Ignore categories whose parent isn't part of the
        # Equipment hierarchy.
        if parent_key not in titles:
            continue

        children.setdefault(parent_key, set()).add(child_key)

    return children, titles


def category_row_scope(
    title: str,
    descendants: dict[str, set[str]],
    titles: dict[str, str],
) -> set[str]:
    """
    Return the category plus all descendants.

    Example:

        Clothing -> clothing + any child categories
    """
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
