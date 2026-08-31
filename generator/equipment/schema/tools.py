from __future__ import annotations

from generator.equipment.schema.common import (
    FieldExtractor,
    context_field,
    damage_type,
    field,
    tier,
)

EQUIPMENT_FIELDS: dict[str, FieldExtractor] = {
    "Icon": context_field("icon"),
    "Name": context_field("name"),
    "Tier": tier,
    "Damage": field("Damage"),
    "Damage Type": damage_type,
}
