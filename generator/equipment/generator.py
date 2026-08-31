import importlib
from pathlib import Path

from .. import icon
from . import category, markdown, scanner

TITLE = "Equipment"


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
    """Discover equipment items with raw Properties."""
    items = []

    for path in scanner.discover_items(assets):
        try:
            properties = scanner.load_properties(path)

            if not properties or not is_player_item(properties):
                continue

            items.append(
                {
                    "path": path,
                    "properties": properties,
                    "category": (
                        category.category_name_for(
                            properties,
                            category_index,
                        )
                        or "Uncategorized"
                    ),
                }
            )
        except Exception as exc:
            print(f"SKIP {path}: {exc}")

    return items


def is_player_item(properties: dict) -> bool:
    """Return True when the item has a non-system player acquisition recipe."""
    recipes = properties.get("InstancedRecipes")

    if not isinstance(recipes, list):
        return False

    for recipe in recipes:
        if not isinstance(recipe, dict):
            continue
        if recipe.get("bIsSystemRecipe", False):
            continue
        if recipe.get("RequiredUnlockable"):
            return True

    return False


def _item_context(
    item: dict,
    icon_index: dict[str, Path],
    icon_out: Path,
) -> dict:
    """Build values supplied to schemas outside Properties."""
    context = {
        "path": item["path"],
        "icon": "",
    }

    icon_path = icon.find_icon(
        item["properties"],
        icon_index,
    )

    if icon_path:
        destination = icon.copy_icon(
            icon_path,
            icon_out,
        )

        context["icon"] = (
            f'<img src="../assets/icons/{destination.name}" '
            f'alt="{item["path"].stem}" width="48">'
        )

    return context


def render_items(
    items: list[dict],
    schema,
    icon_index: dict[str, Path],
    icon_out: Path,
) -> tuple[list[str], list[dict]]:
    """Extract and sort rows using a schema."""
    headers = list(schema.EQUIPMENT_FIELDS)
    rows = []

    for item in items:
        context = _item_context(
            item,
            icon_index,
            icon_out,
        )

        rows.append(
            {
                field: extractor(
                    item["properties"],
                    context,
                )
                for field, extractor in schema.EQUIPMENT_FIELDS.items()
            }
        )

    rows.sort(key=lambda row: str(row.get("Name", "")).lower())

    return headers, rows


def _schema_for(
    slug: str,
    fallback_slug: str | None = None,
):
    """Resolve a schema with an optional parent fallback."""
    schema = load_schema(slug, fallback=False)

    if schema is not None:
        return schema

    if fallback_slug:
        schema = load_schema(
            fallback_slug,
            fallback=False,
        )

        if schema is not None:
            return schema

    return load_schema("default")


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
        category_children.get(group_key, ()),
        key=lambda key: category_titles[key].lower(),
    )

    if not child_keys:
        return {
            group_title: render_items(
                group_items,
                _schema_for(group_slug),
                icon_index,
                icon_out,
            )
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

        sections[child_title] = render_items(
            child_items,
            _schema_for(
                child_slug,
                fallback_slug=group_slug,
            ),
            icon_index,
            icon_out,
        )

    return sections


def generate(
    assets: Path,
    docs: Path,
    icon_out: Path,
    icon_index: dict[str, Path],
) -> dict:
    """Generate equipment documentation."""
    category_index = category.build_category_index(assets)
    category_children, category_titles = category.build_category_hierarchy(assets)

    print(f"Equipment categories indexed: {len(category_titles)}")

    items = discover_items(
        assets,
        category_index,
    )

    pages = []
    equipment_docs = docs / "equipment"
    equipment_docs.mkdir(
        parents=True,
        exist_ok=True,
    )

    group_keys = sorted(
        category_children.get("equipment", ()),
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
            equipment_docs / f"{slug}.md",
            title=title,
            description=f"{total} matching assets",
            sections=sections,
        )

        pages.append(
            {
                "title": title,
                "slug": f"equipment/{slug}.md",
            }
        )

        print(f"\tGENERATED equipment/{slug}.md ({total} items)")

    return {
        "title": TITLE,
        "pages": pages,
    }
