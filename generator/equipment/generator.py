import importlib
from pathlib import Path

from generator.equipment import category, markdown, scanner


def load_schema(slug: str, fallback: bool = True):
    """Load an equipment schema by slug."""
    module_name = f"generator.equipment.schema.{slug}"

    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        if exc.name != module_name:
            raise

        if not fallback:
            return None

        return importlib.import_module("generator.equipment.schema.default")


def render_items(items: list[dict], schema) -> tuple[list[str], list[dict]]:
    """Render equipment items using a schema."""
    headers = list(schema.EQUIPMENT_FIELDS)
    rows = []

    for item in items:
        properties = item["properties"]
        context = item["context"]

        rows.append(
            {
                field: extractor(properties, context)
                for field, extractor in schema.EQUIPMENT_FIELDS.items()
            }
        )

    rows.sort(key=lambda row: str(row.get("Name", "")).lower())

    return headers, rows


def discover_items(
    assets: Path,
    icon_index: dict[str, Path],
    category_index: dict[str, str],
    icon_out: Path,
) -> list[dict]:
    """Discover and extract equipment items."""
    items = []

    for path in scanner.discover_json(assets):
        if not category.is_equipment_item_path(path):
            continue

        try:
            objects = scanner.load_objects(path)
            if not scanner.find_cdo(objects):
                continue

            items.append(
                scanner.generate_equipment_item(
                    path,
                    objects,
                    icon_index,
                    category_index,
                    icon_out,
                )
            )
        except Exception as exc:
            print(f"SKIP {path}: {exc}")

    return items


def build_sections(
    group_key: str,
    group_title: str,
    group_slug: str,
    items: list[dict],
    category_children: dict[str, set[str]],
    category_titles: dict[str, str],
) -> dict[str, tuple[list[str], list[dict]]]:
    """Build Markdown sections for an equipment group."""
    scope = scanner.category_row_scope(
        group_title,
        category_children,
        category_titles,
    )

    group_items = [
        item
        for item in items
        if scanner.normalize_category_key(item["Category"]) in scope
    ]

    child_keys = sorted(
        category_children.get(group_key, set()),
        key=lambda key: category_titles[key].lower(),
    )

    if not child_keys:
        schema = load_schema(group_slug)

        return {
            group_title: render_items(group_items, schema),
        }

    sections = {}

    for child_key in child_keys:
        child_title = category_titles[child_key]
        child_slug = scanner.category_slug(child_title)

        child_scope = scanner.category_row_scope(
            child_title,
            category_children,
            category_titles,
        )

        child_items = [
            item
            for item in group_items
            if scanner.normalize_category_key(item["Category"]) in child_scope
        ]

        schema = load_schema(child_slug, fallback=False)

        if schema is None:
            schema = load_schema(group_slug, fallback=False)

        if schema is None:
            schema = load_schema("default")

        sections[child_title] = render_items(child_items, schema)

    return sections


def generate(
    assets: Path,
    docs: Path,
    icon_out: Path,
    icon_index: dict[str, Path],
) -> list[dict]:
    """Generate equipment documentation and return its index entries."""
    category_index = scanner.build_category_index(assets)

    category_children, category_titles = scanner.build_category_hierarchy(assets)

    print(f"Equipment categories indexed: {len(category_titles)}")

    items = discover_items(
        assets,
        icon_index,
        category_index,
        icon_out,
    )

    pages = []

    group_keys = sorted(
        category_children.get("equipment", set()),
        key=lambda key: category_titles[key].lower(),
    )

    for group_key in group_keys:
        title = category_titles[group_key]
        slug = scanner.category_slug(title)

        sections = build_sections(
            group_key,
            title,
            slug,
            items,
            category_children,
            category_titles,
        )

        total = sum(len(rows) for _, rows in sections.values())

        markdown.write_page(
            docs / f"{slug}.md",
            title=title,
            description=f"{total} matching assets",
            sections=sections,
        )

        pages.append(
            {
                "title": title,
                "slug": slug,
            }
        )

        print(f"\tGENERATED {slug}.md ({total} items)")

    return pages
