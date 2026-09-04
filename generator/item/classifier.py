from __future__ import annotations

from pathlib import Path

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


def is_supporting_family(family: str | None) -> bool:
    return family in {
        "BrokenItems", "KnowledgeBooks", "Loot", "Categories", "ItemGroups"
    }
