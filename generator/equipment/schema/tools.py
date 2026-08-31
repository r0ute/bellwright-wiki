from __future__ import annotations

from generator.schema.common import FieldExtractor, damage_type, field, tier

EQUIPMENT_FIELDS: dict[str, FieldExtractor] = {
    "Icon": lambda _p, ctx: ctx["icon"],
    "Name": lambda _p, ctx: ctx["name"],
    "Tier": tier,
    "Damage": field("Damage"),
    "Damage Type": damage_type,
}
