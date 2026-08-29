from __future__ import annotations
from generator.schemas.common import (
    FieldExtractor,
    damage_type,
    field,
    resolve_path_name,
    nested_field
)

EQUIPMENT_FIELDS: dict[str, FieldExtractor] = {
    "Icon": lambda _p, ctx: ctx["icon"],
    "Name": lambda _p, ctx: ctx["name"],
    "Tier": field("Tier"),
    "Damage Type": damage_type,
    "Damage": field("Damage"),
    "Projectile Damage": nested_field("ProjectileDamage", "Damage"),
    "Rarity": lambda p, _ctx: resolve_path_name(p.get("Rarity")),
}