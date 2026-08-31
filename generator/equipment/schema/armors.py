from __future__ import annotations

from generator.equipment.schema.common import (
    FieldExtractor,
    context_field,
    enum_value,
    field,
    required_skill_value,
    tier,
)

EQUIPMENT_FIELDS: dict[str, FieldExtractor] = {
    "Icon": context_field("icon"),
    "Name": context_field("name"),
    "Tier": tier,
    "Armor Slot": field("ArmorSlot", transform=enum_value),
    "Armor": field("Armor"),
    "Movement Speed Reduction": field("MovementSpeedReduction"),
    "Skill Requirements": field("SkillRequirements", transform=required_skill_value),
}
