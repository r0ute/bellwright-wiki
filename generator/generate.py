from pathlib import Path
import json
import re

from categories import (
    is_equipment_category_path,
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
        category_index[normalize_category_key(path.stem)] = name
        category_index[normalize_category_key(f"{path.stem}_C")] = name

    return category_index


def category_name_for(properties: dict, category_index: dict[str, str]) -> str | None:
    category_ref = properties.get("Category")
    key = category_key_from_ref(category_ref)

    if not key:
        return None

    normalized = normalize_category_key(key)
    return category_index.get(normalized)


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

    return [
        path
        for path in discover_json(assets_root)
        if path.is_relative_to(category_root)
    ]


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
        lines.append(f"- [{category['title']}]({category['slug']}.md)")

    lines.extend([
        "",
        "## Reports",
        "",
        "- [Generation report](generation-report.md)",
        "",
    ])

    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
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

    for path in equipment_category_paths(ASSETS):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue

        objects = raw if isinstance(raw, list) else [raw]
        cdo = find_cdo(objects)
        if not cdo:
            continue

        title = asset_name(path, objects)
        slug = category_slug(path.stem)
        rows = [
            row for row in equipment_items
            if normalize_category_key(row["Category"]) == normalize_category_key(title)
        ]
        rows = sorted(rows, key=lambda row: str(row["Name"]).lower())

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