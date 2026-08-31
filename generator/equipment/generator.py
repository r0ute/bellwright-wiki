import importlib
from pathlib import Path

from .. import icon
from . import category, markdown, scanner


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


def discover_items(
    assets: Path,
    category_index: dict[str, str],
) -> list[dict]:
    """Discover equipment items and retain raw properties."""
    items = []

    for path in scanner.discover_json(assets):
        if not category.is_equipment_item_path(path):
            continue

        try:
            objects = scanner.load_objects(path)
            cdo = scanner.find_cdo(objects)

            if not cdo:
                continue

            properties = cdo.get("Properties")

            if not isinstance(properties, dict):
                continue

            category_name = (
                category.category_name_for(
                    properties,
                    category_index,
                )
                or "Uncategorized"
            )

            items.append(
                {
                    "path": path,
                    "properties": properties,
                    "category": category_name,
                }
            )
        except Exception as exc:
            print(f"SKIP {path}: {exc}")

    return items


def render_items(
    items: list[dict],
    schema,
    icon_index: dict[str, Path],
    icon_out: Path,
) -> tuple[list[str], list[dict]]:
    """Extract and sort equipment rows using a schema."""
    headers = list(schema.EQUIPMENT_FIELDS)
    rows = []

    for item in items:
        properties = item["properties"]
        path = item["path"]

        icon_path = icon.find_icon(
            properties,
            icon_index,
        )

        icon_md = ""

        if icon_path:
            destination = icon.copy_icon(
                icon_path,
                icon_out,
            )

            icon_md = (
                f'<img src="assets/icons/{destination.name}" '
                f'alt="{path.stem}" width="48">'
            )

        context = {
            "icon": icon_md,
            "path": path,
        }

        row = {
            field: extractor(properties, context)
            for field, extractor in schema.EQUIPMENT_FIELDS.items()
        }

        rows.append(row)

    rows.sort(key=lambda row: str(row.get("Name", "")).lower())

    return headers, rows


def resolve_schema(
    slug: str,
    fallback_slug: str | None = None,
):
    """Resolve child, group, then default schema."""
    schema = load_schema(slug, fallback=False)

    if schema is None and fallback_slug:
        schema = load_schema(
            fallback_slug,
            fallback=False,
        )

    return schema or load_schema("default")


def build_sections(
    group_key: str,
    group_title: str,
    group_slug: str,
    items: list[dict],
    category_children: dict[str, set[str]],
    category_titles: dict[str, str],
    icon_index: dict[str, Path],
    icon_out: Path,
) -> dict[str, tuple[list[str], list[dict]]]:
    """Build Markdown sections for an equipment group."""
    scope = category.category_row_scope(
        group_title,
        category_children,
        category_titles,
    )

    group_items = [
        item
        for item in items
        if category.normalize_category_key(item["category"]) in scope
    ]

    child_keys = sorted(
        category_children.get(group_key, set()),
        key=lambda key: category_titles[key].lower(),
    )

    if not child_keys:
        schema = load_schema(group_slug)

        return {
            group_title: render_items(
                group_items,
                schema,
                icon_index,
                icon_out,
            ),
        }

    sections = {}

    for child_key in child_keys:
        child_title = category_titles[child_key]
        child_slug = category.category_slug(child_title)

        child_scope = category.category_row_scope(
            child_title,
            category_children,
            category_titles,
        )

        child_items = [
            item
            for item in group_items
            if category.normalize_category_key(item["category"]) in child_scope
        ]

        schema = resolve_schema(
            child_slug,
            fallback_slug=group_slug,
        )

        sections[child_title] = render_items(
            child_items,
            schema,
            icon_index,
            icon_out,
        )

    return sections


def generate(
    assets: Path,
    docs: Path,
    icon_out: Path,
    icon_index: dict[str, Path],
) -> list[dict]:
    """Generate equipment documentation."""
    category_index = scanner.build_category_index(assets)

    category_children, category_titles = scanner.build_category_hierarchy(assets)

    print(f"Equipment categories indexed: {len(category_titles)}")

    items = discover_items(
        assets,
        category_index,
    )

    pages = []

    group_keys = sorted(
        category_children.get("equipment", set()),
        key=lambda key: category_titles[key].lower(),
    )

    for group_key in group_keys:
        title = category_titles[group_key]
        slug = category.category_slug(title)

        sections = build_sections(
            group_key,
            title,
            slug,
            items,
            category_children,
            category_titles,
            icon_index,
            icon_out,
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
