import importlib
import json
from pathlib import Path

from generator import categories, icons, renderer, scanner
from generator import markdown as md


def load_objects(path: Path) -> list[dict]:
    raw = json.loads(path.read_text(encoding="utf-8"))

    if isinstance(raw, list):
        return [obj for obj in raw if isinstance(obj, dict)]

    if isinstance(raw, dict):
        return [raw]

    return []


def load_schema(slug: str, fallback: bool = True):
    try:
        return importlib.import_module(f"generator.schemas.{slug}")
    except ImportError:
        if not fallback:
            return None

        try:
            return importlib.import_module("generator.schemas.default")
        except ImportError:
            return None


def render_items(
    items: list[dict],
    schema,
) -> tuple[list[str], list[dict]]:
    if schema is None:
        headers = ["Icon", "Name", "Category", "Price"]

        rows = [
            {
                "Icon": item["context"]["icon"],
                "Name": item["context"]["name"],
                "Category": item["Category"],
                "Price": (
                    item["properties"].get("ExpectedPrice")
                    or item["properties"].get("Price")
                    or ""
                ),
            }
            for item in items
        ]
    else:
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
    assets = scanner.ASSETS
    docs = scanner.DOCS
    icon_out = scanner.ICON_OUT

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

    icon_index = icons.build_icon_index(assets)
    category_index = scanner.build_category_index(assets)

    category_children, category_titles = scanner.build_category_hierarchy(assets)

    category_paths = scanner.equipment_category_paths(assets)

    print(f"Icons indexed: {len(icon_index)}")
    print(f"Categories indexed: {len(category_titles)}")

    # ------------------------------------------------------------
    # Equipment items
    # ------------------------------------------------------------

    equipment_items = []

    for path in scanner.discover_json(assets):
        if not categories.is_equipment_item_path(path):
            continue

        try:
            objects = load_objects(path)
        except Exception as exc:
            print(f"SKIP {path}: {exc}")
            continue

        if not scanner.find_cdo(objects):
            continue

        try:
            item = scanner.generate_equipment_item(
                path,
                objects,
                icon_index,
                category_index,
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
        slug = scanner.category_slug(title)

        # All descendants belong to this group.
        scope = scanner.category_row_scope(
            title,
            category_children,
            category_titles,
        )

        group_items = [
            item
            for item in equipment_items
            if scanner.normalize_category_key(item["Category"]) in scope
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

                child_scope = scanner.category_row_scope(
                    child_title,
                    category_children,
                    category_titles,
                )

                items = [
                    item
                    for item in group_items
                    if scanner.normalize_category_key(item["Category"]) in child_scope
                ]

                # Try the child's own schema first.
                schema = load_schema(
                    scanner.category_slug(child_title),
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

        md.write_page(
            docs / f"{slug}.md",
            title=title,
            description=f"{total} matching assets.",
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
    )


if __name__ == "__main__":
    main()
