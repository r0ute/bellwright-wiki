from pathlib import Path
import json
import re

from categories import (
    category_name_for_path,
    is_equipment_category_path,
    is_equipment_category_group,
    is_equipment_item_path,
)
from discover import discover_json
from icons import build_icon_index, copy_icon, find_icon
from markdown import write_generation_report, write_page
from schemas.weapons import EQUIPMENT_FIELDS


ROOT = Path(__file__).resolve().parent.parent

ASSETS = ROOT / "assets"
DOCS = ROOT / "docs"
ICON_OUT = DOCS / "assets" / "icons"


def find_cdo(objects: list) -> dict | None:
    return next(
        (
            obj
            for obj in objects
            if isinstance(obj, dict)
            and isinstance(obj.get("Properties"), dict)
        ),
        None,
    )


def asset_name(path: Path, objects: list) -> str:
    cdo = find_cdo(objects)

    if not cdo:
        return path.stem

    name = cdo["Properties"].get("Name")

    if isinstance(name, dict):
        return (
            name.get("LocalizedString")
            or name.get("SourceString")
            or path.stem
        )

    if isinstance(name, str) and name:
        return name

    return path.stem


def normalize_category_key(value: str) -> str:
    cleaned = value.strip()

    if cleaned.endswith("_C"):
        cleaned = cleaned[:-2]

    return re.sub(r"[^a-z0-9]", "", cleaned.lower())


def category_key_from_ref(value: object) -> str | None:
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


def build_category_index(assets_root: Path) -> dict[str, str]:
    category_index: dict[str, str] = {}

    for path in discover_json(assets_root):
        if not is_equipment_category_path(path):
            continue

        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue

        objects = raw if isinstance(raw, list) else [raw]
        cdo = find_cdo(objects)

        if not cdo:
            continue

        name = asset_name(path, objects)
        category_index[normalize_category_key(name)] = name
        category_index[normalize_category_key(path.stem)] = name
        category_index[normalize_category_key(f"{path.stem}_C")] = name

    return category_index


def category_name_for(properties: dict, category_index: dict[str, str]) -> str | None:
    category_ref = properties.get("Category")
    key = category_key_from_ref(category_ref)

    if not key:
        return None

    normalized = normalize_category_key(key)
    # Direct match first
    title = category_index.get(normalized)
    if title:
        return title

    # Fallback: if an exact category file for the referenced key doesn't
    # exist, try matching it to a parent/group category by prefix. For
    # example, Ammo_Arrows -> matches the Ammo group that was indexed.
    for candidate_key, candidate_title in sorted(category_index.items(), key=lambda it: -len(it[0])):
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

    properties = cdo["Properties"]

    name = asset_name(path, objects)
    category_name = category_name_for(properties, category_index) or "Uncategorized"

    icon = find_icon(properties, icon_index)

    icon_md = "—"

    if icon:
        destination = copy_icon(icon, ICON_OUT)

        icon_md = (
            f'<img src="assets/icons/{destination.name}" '
            f'alt="{name}" width="48">'
        )

    context = {
        "name": name,
        "icon": icon_md,
        "path": path,
    }

    row = {
        field: extractor(properties, context)
        for field, extractor in EQUIPMENT_FIELDS.items()
    }
    row["Category"] = category_name
    return row


def category_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "category"


def equipment_category_paths(assets_root: Path) -> list[Path]:
    category_root = assets_root / "Bellwright" / "Content" / "Mist" / "Data" / "Items" / "Categories" / "Equipment"
    if not category_root.exists():
        return []

    seen: set[str] = set()
    paths: list[Path] = []

    for path in sorted(discover_json(assets_root), key=lambda item: str(item).lower()):
        if not path.is_relative_to(category_root):
            continue

        title = category_name_for_path(path)
        if not title:
            continue

        key = normalize_category_key(title)
        if key in seen:
            continue

        seen.add(key)
        paths.append(path)

    return paths


def build_category_hierarchy(assets_root: Path) -> tuple[dict[str, set[str]], dict[str, str]]:
    titles: dict[str, str] = {}
    paths: list[Path] = []

    for path in discover_json(assets_root):
        if not is_equipment_category_path(path):
            continue

        title = category_name_for_path(path)
        if not title:
            continue

        key = normalize_category_key(title)
        titles[key] = title
        paths.append(path)

    children: dict[str, set[str]] = {key: set() for key in titles}

    for path in paths:
        title = category_name_for_path(path)
        if not title:
            continue

        key = normalize_category_key(title)

        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue

        objects = raw if isinstance(raw, list) else [raw]
        for obj in objects:
            if not isinstance(obj, dict):
                continue
            props = obj.get("Properties")
            if not isinstance(props, dict):
                continue
            parent = props.get("Parent")
            if not isinstance(parent, dict):
                continue

            parent_key = category_key_from_ref(parent)
            if not parent_key:
                continue

            parent_key = normalize_category_key(parent_key)
            if not parent_key:
                continue

            if parent_key not in titles:
                parent_key = "equipment"

            children.setdefault(parent_key, set()).add(key)

    if "equipment" not in children:
        children["equipment"] = set(titles)

    return children, titles


def category_row_scope(title: str, descendants: dict[str, set[str]], titles: dict[str, str]) -> set[str]:
    start = normalize_category_key(title)
    scope: set[str] = set()
    stack = [start]

    while stack:
        current = stack.pop()
        if current in scope:
            continue
        scope.add(current)
        stack.extend(sorted(descendants.get(current, set()), key=str.lower, reverse=True))

    return scope


def write_index_page(output: Path, categories: list[dict]) -> None:
    lines = [
        "---",
        "layout: default",
        "title: Bellwright Data",
        "---",
        "",
        "# Bellwright Data",
        "",
        "## Categories",
        "",
    ]

    for category in sorted(categories, key=lambda item: item["title"].lower()):
        lines.append(
            f'- [{category["title"]}]({category["slug"]})'
        )

    lines.extend([
        "",
        "## Reports",
        "",
        "- [Generation report](generation-report)",
        "",
    ])

    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    for stale in DOCS.glob("*.md"):
        stale.unlink()

    print(f"Assets: {ASSETS}")
    print(f"Docs:   {DOCS}")

    icon_index = build_icon_index(ASSETS)
    category_index = build_category_index(ASSETS)

    print(f"Icons indexed: {len(icon_index)}")
    print(f"Categories indexed: {len(category_index)}")

    equipment_items = []
    scanned = 0
    category_pages: list[dict] = []
    seen_category_slugs: set[str] = set()

    for path in discover_json(ASSETS):
        scanned += 1

        if not is_equipment_item_path(path):
            continue

        try:
            raw = json.loads(
                path.read_text(encoding="utf-8")
            )
        except Exception as exc:
            print(f"SKIP {path}: {exc}")
            continue

        if not isinstance(raw, list):
            raw = [raw]

        if not find_cdo(raw):
            continue

        equipment_items.append(
            generate_equipment_item(
                path,
                raw,
                icon_index,
                category_index,
            )
        )

    headers = list(EQUIPMENT_FIELDS)
    category_children, category_titles = build_category_hierarchy(ASSETS)

    processed_keys: set[str] = set()

    # Collect category paths once and build a quick lookup
    category_paths = list(equipment_category_paths(ASSETS))

    # Map normalized title -> path (useful if needed)
    path_by_key: dict[str, Path] = {}
    for path in category_paths:
        title = category_name_for_path(path)
        if not title:
            continue
        path_by_key[normalize_category_key(title)] = path

    # Phase 1: emit pages for category groups (standalone .md with sections)
    for path in sorted(category_paths, key=lambda p: str(p).lower()):
        if not is_equipment_category_group(path):
            continue

        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue

        objects = raw if isinstance(raw, list) else [raw]
        cdo = find_cdo(objects)
        if not cdo:
            continue

        title = asset_name(path, objects)
        key = normalize_category_key(title)
        if key in processed_keys:
            continue

        slug = category_slug(path.stem)

        # Build sections: if the group has child categories, emit only
        # the child-category tables. If the group has no children, emit a
        # single table for the group (full scope).
        sections: dict[str, list[dict]] = {}

        child_keys = sorted(category_children.get(key, set()), key=lambda k: category_titles.get(k, ""))

        if child_keys:
            # Emit only child sections; do not include a group's own table.
            for child_key in child_keys:
                child_title = category_titles.get(child_key)
                if not child_title:
                    continue

                child_path = path_by_key.get(child_key)
                # If the child is itself a category group file, skip it here
                # so that it will be emitted as its own standalone page later.
                if child_path and is_equipment_category_group(child_path):
                    continue

                child_scope = category_row_scope(child_title, category_children, category_titles)
                child_rows = [
                    row for row in equipment_items
                    if normalize_category_key(row["Category"]) in child_scope
                ]
                child_rows = sorted(child_rows, key=lambda row: str(row["Name"]).lower())
                sections[child_title] = child_rows
                processed_keys.add(child_key)

            # Mark the group as processed so it won't be emitted separately.
            processed_keys.add(key)
        else:
            # No child categories: emit a full-scope table for the group.
            group_scope = category_row_scope(title, category_children, category_titles)
            group_rows = [
                row for row in equipment_items
                if normalize_category_key(row["Category"]) in group_scope
            ]
            group_rows = sorted(group_rows, key=lambda row: str(row["Name"]).lower())
            sections[title] = group_rows
            processed_keys.add(key)

        total = sum(len(r) for r in sections.values())
        if slug not in seen_category_slugs:
            category_pages.append({"title": title, "slug": slug})
            seen_category_slugs.add(slug)

        write_page(
            DOCS / f"{slug}.md",
            title=title,
            description=(
                f"{total} matching assets in the {title} category."
            ),
            headers=headers,
            sections=sections,
        )

    # Phase 2: emit pages for remaining non-group categories
    for path in sorted(category_paths, key=lambda p: str(p).lower()):
        if is_equipment_category_group(path):
            continue

        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue

        objects = raw if isinstance(raw, list) else [raw]
        cdo = find_cdo(objects)
        if not cdo:
            continue

        title = asset_name(path, objects)
        key = normalize_category_key(title)
        if key in processed_keys:
            continue

        slug = category_slug(path.stem)
        scope = category_row_scope(title, category_children, category_titles)
        rows = [
            row for row in equipment_items
            if normalize_category_key(row["Category"]) in scope
        ]
        rows = sorted(rows, key=lambda row: str(row["Name"]).lower())

        processed_keys.add(key)

        if slug not in seen_category_slugs:
            category_pages.append({"title": title, "slug": slug})
            seen_category_slugs.add(slug)

        write_page(
            DOCS / f"{slug}.md",
            title=title,
            description=(
                f"{len(rows)} matching assets in the {title} category."
            ),
            headers=headers,
            rows=rows,
        )

    write_index_page(DOCS / "index.md", category_pages)

    icons_found = sum(
        item["Icon"] != "—"
        for item in equipment_items
    )

    write_generation_report(
        DOCS / "generation-report.md",
        scanned=scanned,
        generated=len(equipment_items),
        icons_found=icons_found,
    )

    print(
        f"Scanned {scanned}; "
        f"generated {len(equipment_items)} equipment items; "
        f"icons {icons_found}."
    )


if __name__ == "__main__":
    main()