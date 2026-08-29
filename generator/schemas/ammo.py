from __future__ import annotations

from generator.schemas.common import (
    FieldExtractor,
    asset_reference_name,
    damage_type,
    field,
    nested_field,
    tier,
)

EQUIPMENT_FIELDS: dict[str, FieldExtractor] = {
    "Icon": lambda _p, ctx: ctx["icon"],
    "Name": lambda _p, ctx: ctx["name"],
    "Tier": tier,
    "Category": lambda p, _ctx: asset_reference_name(p.get("Category")),
    "Damage Type": damage_type,
    "Damage": field("Damage"),
    "ProjectileDamage": nested_field("ProjectileDamage", "Damage"),
}
