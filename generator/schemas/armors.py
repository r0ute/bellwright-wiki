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
    "B Hide Corresponding Bodypart": field("bHideCorrespondingBodypart"),
    "B Hide Upper Default Clothing": field("bHideUpperDefaultClothing"),
    "B Hide Lower Default Clothing": field("bHideLowerDefaultClothing"),
    "Equipped Mesh": field("EquippedMesh"),
    "Female Equipped Mesh": field("FemaleEquippedMesh"),
    "Equipped Mesh Attach Socket": field("EquippedMeshAttachSocket"),
    "Phys Material": field("PhysMaterial"),
}