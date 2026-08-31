from __future__ import annotations

from generator.equipment.schema.common import (
    FieldExtractor,
    asset_reference_name,
    context_field,
    damage_type,
    field,
    nested_field,
    tier,
)

EQUIPMENT_FIELDS: dict[str, FieldExtractor] = {
    "Icon": context_field("icon"),
    "Name": context_field("name"),
    "Tier": tier,
    "Category": field("Category", transform=asset_reference_name),
    "Damage Type": damage_type,
    "Damage": field("Damage"),
    "Projectile Damage": nested_field("ProjectileDamage", "Damage"),
}
