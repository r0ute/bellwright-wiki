from __future__ import annotations

import importlib
from collections import defaultdict
from pathlib import Path
from typing import Any

from .. import icon
from . import category, markdown, scanner
from .model import Item
from .schema.common import FieldExtractor

TITLE = "Items"

RESOURCE_SCHEMAS = {
    "MistConsumableItemTemplate": "consumable",
    "MistCarcassItemTemplate": "carcass",
    "MistSeedItemTemplate": "seed",
    "MistBaitItemTemplate": "bait",
    "MistItemTemplate": "resource",
}

FAMILY_TITLES = {
    "Equipment": "Equipment",
    "Resources": "Resources",
    "UniqueQuestItems": "Unique Quest Items",
    "PlaceableDecorations": "Placeable Decorations",
    "Special": "Special",
    "UniqueQuestItemsRaidMap": "Unique Quest Items (Raid Map)",
    "Fishes": "Fish",
    "Healing": "Healing",
}

FAMILY_SCHEMAS = {
    "UniqueQuestItems": "unique_quest_items",
    "PlaceableDecorations": "placeable_decorations",
    "Special": "special",
    "UniqueQuestItemsRaidMap": "unique_quest_items_raid_map",
    "Fishes": "fishes",
    "Healing": "healing",
}


def _load_module(module_name: str):
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        if exc.name != module_name:
            raise
        return None


def _schema_for(item: Item):
    if item.family == "Equipment":
        slug = category.CategoryIndex.slug(item.category)
        return _load_module(f"generator.item.schema.equipment.{slug}") or _load_module(
            "generator.item.schema.equipment.default"
        )

    if item.family == "Resources":
        slug = RESOURCE_SCHEMAS.get(item.template, "resource")
        return _load_module(f"generator.item.schema.resources.{slug}") or _load_module(
            "generator.item.schema.resources.resource"
        )

    module_name = FAMILY_SCHEMAS.get(item.family)
    if module_name:
        return _load_module(f"generator.item.schema.{module_name}")

    return _load_module("generator.item.schema.default")


def _fields_for(item: Item) -> dict[str, FieldExtractor]:
    schema = _schema_for(item)
    if schema is None:
        return {}
    return dict(getattr(schema, "FIELDS", {}))


def _item_context(
    item: Item,
    icon_index: dict[str, Path],
    icon_out: Path,
) -> dict[str, Any]:
    context = {
        "path": item.path,
        "family": item.family,
        "template": item.template,
        "category": item.category,
        "icon": "",
        "damaged_item": item.damaged_item,
        "unbroken_parent": item.unbroken_parent,
    }

    icon_path = icon.find_icon(item.properties, icon_index)

    if icon_path:
        destination = icon.copy_icon(icon_path, icon_out)
        context["icon"] = (
            f'<img src="../assets/icons/{destination.name}" '
            f'alt="{item.stem}" width="48">'
        )

    return context


def _relationship_maps(
    assets: Path,
) -> tuple[dict[str, str], dict[str, str]]:
    by_parent: dict[str, str] = {}
    by_broken: dict[str, str] = {}

    for broken_asset, (damaged, parent) in scanner.load_broken_relationships(
        assets
    ).items():
        damaged = damaged or broken_asset

        if parent:
            by_parent[parent] = damaged

        by_broken[damaged] = parent

    return by_parent, by_broken


def _apply_relationships(items: list[Item], assets: Path) -> None:
    by_parent, by_broken = _relationship_maps(assets)

    for item in items:
        item.damaged_item = by_parent.get(item.stem, "")
        item.unbroken_parent = by_broken.get(item.stem, "")


def _rows(
    items: list[Item],
    icon_index: dict[str, Path],
    icon_out: Path,
) -> tuple[list[str], list[dict[str, Any]]]:
    if not items:
        return [], []

    field_sets = [_fields_for(item) for item in items]

    # Schema modules own their complete field sets. The generator only
    # preserves first-seen schema order when a section contains more than
    # one schema variant (for example, Resources by template).
    headers: list[str] = []
    for fields in field_sets:
        for name in fields:
            if name not in headers:
                headers.append(name)

    rows: list[dict[str, Any]] = []

    for item, fields in zip(items, field_sets):
        context = _item_context(item, icon_index, icon_out)
        rows.append(
            {
                name: extractor(item.properties, context)
                for name, extractor in fields.items()
            }
        )

    rows.sort(key=lambda row: str(row.get("Name", "")).lower())

    return headers, rows


def _equipment_sections(
    items: list[Item],
    category_index: category.CategoryIndex,
    icon_index: dict[str, Path],
    icon_out: Path,
):
    sections: dict[str, tuple[list[str], list[dict]]] = {}
    groups = category_index.child_titles("Equipment") or ["Equipment"]

    for title in groups:
        scope = category_index.scope(title)
        group_items = [
            item
            for item in items
            if category.normalize_category_key(item.category) in scope
        ]
        if group_items:
            sections[title] = _rows(group_items, icon_index, icon_out)

    if not sections and items:
        sections["Uncategorized"] = _rows(items, icon_index, icon_out)

    return sections


def _resource_sections(
    items: list[Item],
    icon_index: dict[str, Path],
    icon_out: Path,
):
    template_titles = {
        "MistItemTemplate": "Resources",
        "MistConsumableItemTemplate": "Consumables",
        "MistCarcassItemTemplate": "Carcasses",
        "MistSeedItemTemplate": "Seeds",
        "MistBaitItemTemplate": "Bait",
    }

    groups: dict[str, list[Item]] = defaultdict(list)
    for item in items:
        title = template_titles.get(item.template, item.template or "Other")
        groups[title].append(item)

    return {
        title: _rows(group, icon_index, icon_out)
        for title, group in sorted(groups.items(), key=lambda pair: pair[0].lower())
    }


def _family_sections(
    items: list[Item],
    icon_index: dict[str, Path],
    icon_out: Path,
):
    groups: dict[str, list[Item]] = defaultdict(list)
    for item in items:
        groups[item.category or "Uncategorized"].append(item)

    return {
        title: _rows(group, icon_index, icon_out)
        for title, group in sorted(groups.items(), key=lambda pair: pair[0].lower())
    }


def generate(
    assets: Path,
    docs: Path,
    icon_out: Path,
    icon_index: dict[str, Path],
) -> dict:
    """Generate all supported item families from Items/."""
    category_index = category.build_category_index(assets)
    items = list(scanner.discover_items(assets, category_index))
    _apply_relationships(items, assets)

    by_family: dict[str, list[Item]] = defaultdict(list)
    for item in items:
        by_family[item.family].append(item)

    pages = []
    for family, title in FAMILY_TITLES.items():
        family_items = by_family.get(family, [])
        if not family_items:
            continue

        if family == "Equipment":
            sections = _equipment_sections(
                family_items, category_index, icon_index, icon_out
            )
        elif family == "Resources":
            sections = _resource_sections(family_items, icon_index, icon_out)
        else:
            sections = _family_sections(family_items, icon_index, icon_out)

        slug = category.CategoryIndex.slug(title)
        output = docs / "items" / f"{slug}.md"
        markdown.write_page(output, title=title, sections=sections)
        pages.append({"title": title, "slug": f"items/{slug}"})

        total = sum(len(rows) for _, rows in sections.values())
        print(f"\tGENERATED items/{slug}.md ({total} items)")

    print(f"Item definitions discovered: {len(items)}")
    return {"title": TITLE, "pages": pages}
