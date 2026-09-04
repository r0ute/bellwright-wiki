from __future__ import annotations

from pathlib import Path

from .category import normalize_category_key

FAMILY_NAMES = {
    "Equipment",
    "Resources",
    "BrokenItems",
    "KnowledgeBooks",
    "Loot",
    "UniqueQuestItems",
    "PlaceableDecorations",
    "Special",
    "UniqueQuestItemsRaidMap",
    "Fishes",
    "Healing",
    "Categories",
    "ItemGroups",
}

GENERATED_FAMILIES = {
    "Equipment",
    "Resources",
    "UniqueQuestItems",
    "PlaceableDecorations",
    "Special",
    "UniqueQuestItemsRaidMap",
    "Fishes",
    "Healing",
}

SUPPORTING_FAMILIES = {
    "BrokenItems",
    "KnowledgeBooks",
    "Loot",
    "Categories",
    "ItemGroups",
}


def family_for_path(path: Path) -> str | None:
    """Return the top-level Items family for a JSON path."""
    parts = path.parts
    lowered = [part.lower() for part in parts]

    try:
        index = lowered.index("items")
    except ValueError:
        return None

    if index + 1 >= len(parts):
        return None

    raw_family = parts[index + 1]
    lookup = {name.lower(): name for name in FAMILY_NAMES}

    return lookup.get(raw_family.lower())


def family_for_category(
    category: str | None,
    *,
    category_index=None,
) -> str | None:
    """
    Return the semantic family represented by an item category.

    Category hierarchy is authoritative over the physical source
    directory. For example, TwoHanded is a descendant of Equipment,
    so an item stored in UniqueQuestItems but categorized as TwoHanded
    is generated as Equipment.
    """
    if not category or category_index is None:
        return None

    normalized = normalize_category_key(category)

    equipment_scope = category_index.scope("Equipment")

    if normalized in equipment_scope:
        return "Equipment"

    return None


def classify_item_family(
    path: Path,
    category: str | None,
    *,
    category_index=None,
) -> str | None:
    """
    Determine the generated family for an item.

    Semantic category takes precedence over the source directory.
    The source directory remains the fallback for categories that
    do not currently map to a semantic family.
    """
    semantic_family = family_for_category(
        category,
        category_index=category_index,
    )

    if semantic_family:
        return semantic_family

    return family_for_path(path)


def is_generated_family(family: str | None) -> bool:
    return family in GENERATED_FAMILIES


def is_supporting_family(family: str | None) -> bool:
    return family in SUPPORTING_FAMILIES
