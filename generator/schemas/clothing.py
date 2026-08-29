from __future__ import annotations

from generator.schemas.common import (
    FieldExtractor,
    enum_value,
    field,
    tier,
)

EQUIPMENT_FIELDS: dict[str, FieldExtractor] = {
    "Icon": lambda _p, ctx: ctx["icon"],
    "Name": lambda _p, ctx: ctx["name"],
    "Tier": tier,
    "Armor Slot": lambda p, _ctx: enum_value(p.get("ArmorSlot")),
    "Armor": field("Armor"),
}
