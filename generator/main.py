import importlib
import json
from pathlib import Path

from generator import icon, renderer
from generator.equipment import category as equipment_category
from generator.equipment import markdown as equipment_markdown
from generator.equipment import scanner as equipment_scanner

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
ASSETS = ROOT / "assets"
ICON_OUT = DOCS / "assets" / "icons"


def load_objects(path: Path) -> list[dict]:
    raw = json.loads(path.read_text(encoding="utf-8"))

    if isinstance(raw, list):
        return [obj for obj in raw if isinstance(obj, dict)]

    if isinstance(raw, dict):
        return [raw]

    return []


def load_schema(slug: str, fallback: bool = True):
    try:
        return importlib.import_module(f"generator.equipment.schema.{slug}")
    except ModuleNotFoundError as exc:
        if exc.name != f"generator.equipment.schema.{slug}":
            raise

        if not fallback:
            return None

        return importlib.import_module("generator.equipment.schema.default")


def render_items(
    items: list[dict],
    schema,
) -> tuple[list[str], list[dict]]:
    if schema:
        headers = list(schema.EQUIPMENT_FIELDS.keys())
        rows = []

        for item in items:
            row = {}

            for field, extractor in schema.EQUIPMENT_FIELDS.items():
                try:
                    row[field] = extractor(
                        item["properties"],
                        item["context"],
                    )
                except Exception:
                    row[field] = ""

            rows.append(row)

    rows.sort(key=lambda row: str(row.get("Name", "")).lower())

    return headers, rows


def main() -> None:
    assets = ASSETS
    docs = DOCS
    icon_out = ICON_OUT

    docs.mkdir(parents=True, exist_ok=True)

    # Remove generated markdown files from previous runs.
    for path in docs.glob("*.md"):
        path.unlink()

    # Remove generated icons from previous runs.
    if icon_out.exists():
        for path in icon_out.iterdir():
            if path.is_file():
                path.unlink()

    print(f"Assets: {assets}")
    print(f"Docs:   {docs}")

    # ------------------------------------------------------------
    # Indexes
    # ------------------------------------------------------------

    icon_index = icon.build_icon_index(assets)
    category_index = equipment_scanner.build_category_index(assets)

    category_children, category_titles = equipment_scanner.build_category_hierarchy(
        assets
    )

    print(f"Icons indexed: {len(icon_index)}")
    print(f"Categories indexed: {len(category_titles)}")

    # ------------------------------------------------------------
    # Equipment items
    # ------------------------------------------------------------

    equipment_items = []

    for path in equipment_scanner.discover_json(assets):
        if not equipment_category.is_equipment_item_path(path):
            continue

        try:
            objects = load_objects(path)
        except Exception as exc:
            print(f"SKIP {path}: {exc}")
            continue

        if not equipment_scanner.find_cdo(objects):
            continue

        try:
            item = equipment_scanner.generate_equipment_item(
                path, objects, icon_index, category_index, icon_out
            )
        except Exception as exc:
            print(f"SKIP {path}: {exc}")
            continue

        equipment_items.append(item)

    # ------------------------------------------------------------
    # Top-level Equipment groups
    # ------------------------------------------------------------

    group_keys = sorted(
        category_children.get("equipment", set()),
        key=lambda key: category_titles[key].lower(),
    )

    category_pages = []

    for group_key in group_keys:
        title = category_titles[group_key]
        slug = equipment_scanner.category_slug(title)

        # All descendants belong to this group.
        scope = equipment_scanner.category_row_scope(
            title,
            category_children,
            category_titles,
        )

        group_items = [
            item
            for item in equipment_items
            if equipment_scanner.normalize_category_key(item["Category"]) in scope
        ]

        sections = {}

        child_keys = sorted(
            category_children.get(group_key, set()),
            key=lambda key: category_titles[key].lower(),
        )

        if child_keys:
            # One table per child category.
            for child_key in child_keys:
                child_title = category_titles[child_key]

                child_scope = equipment_scanner.category_row_scope(
                    child_title,
                    category_children,
                    category_titles,
                )

                items = [
                    item
                    for item in group_items
                    if equipment_scanner.normalize_category_key(item["Category"])
                    in child_scope
                ]

                # Try the child's own schema first.
                schema = load_schema(
                    equipment_scanner.category_slug(child_title),
                    fallback=False,
                )

                # If no child-specific schema exists, use the group's schema.
                if schema is None:
                    schema = load_schema(
                        slug,
                        fallback=False,
                    )

                # Only now fall back to default.py.
                if schema is None:
                    schema = load_schema("default")

                headers, rows = render_items(items, schema)

                sections[child_title] = (headers, rows)

        else:
            # Group has no children: use the group's own schema,
            # then default.py.
            schema = load_schema(
                slug,
                fallback=False,
            )

            if schema is None:
                schema = load_schema("default")

            headers, rows = render_items(group_items, schema)

            sections[title] = (headers, rows)

        total = sum(len(rows) for _, rows in sections.values())

        equipment_markdown.write_page(
            docs / f"{slug}.md",
            title=title,
            description=f"{total} matching assets",
            sections=sections,
        )

        category_pages.append(
            {
                "title": title,
                "slug": slug,
            }
        )

        print(f"GENERATED {slug}.md ({total} items)")

    # ------------------------------------------------------------
    # Index
    # ------------------------------------------------------------

    renderer.write_index_page(
        docs / "index.md",
        category_pages,
        assets / "T_Logo.webp",
    )


if __name__ == "__main__":
    main()
