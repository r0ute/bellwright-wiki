from __future__ import annotations

from generator.equipment.schema.common import FieldExtractor, context_field, field, tier

EQUIPMENT_FIELDS: dict[str, FieldExtractor] = {
    "Icon": context_field("icon"),
    "Name": context_field("name"),
    "Category": field("Category"),
    "Tier": tier,
}
