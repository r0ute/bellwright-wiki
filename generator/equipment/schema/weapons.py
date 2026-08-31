from __future__ import annotations

from generator.equipment.schema.common import (
    FieldExtractor,
    asset_reference_name,
    field,
    tier,
)

EQUIPMENT_FIELDS: dict[str, FieldExtractor] = {
    "Icon": lambda _p, ctx: ctx["icon"],
    "Name": lambda _p, ctx: ctx["name"],
    "Tier": tier,
    "Rarity": lambda p, _ctx: asset_reference_name(p.get("Rarity")),
    "Damage": field("Damage"),
    "Speed": field("WeaponSpeed"),
    "Length": field("WeaponLength"),
}
