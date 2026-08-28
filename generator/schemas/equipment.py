from __future__ import annotations
from typing import Any
try:
    from generator.schemas.common import (
        FieldExtractor,
        extract_value,
        field,
    )
except ModuleNotFoundError:
    from schemas.common import (
        FieldExtractor,
        extract_value,
        field,
    )

EQUIPMENT_FIELDS: dict[str, FieldExtractor] = {
    "Icon": lambda _p, ctx: ctx['icon'],
    "Name": lambda _p, ctx: ctx['name'],
    "Armor Slot": field("ArmorSlot"),
    "Component Class": field("ComponentClass"),
    "Phys Material": field("PhysMaterial"),
    "Sound Category": field("SoundCategory"),
    "Rarity": field("Rarity"),
    "B Repairable": field("bRepairable"),
    "Codex Entry": field("CodexEntry"),
    "B Ignore Container Max Stack Size": field("bIgnoreContainerMaxStackSize"),
}