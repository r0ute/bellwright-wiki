from __future__ import annotations

from generator.schema.common import (
    FieldExtractor,
    enum_value,
    field,
    required_skill_value,
    tier,
)

EQUIPMENT_FIELDS: dict[str, FieldExtractor] = {
    "Icon": lambda _p, ctx: ctx["icon"],
    "Name": lambda _p, ctx: ctx["name"],
    "Tier": tier,
    "Armor Slot": lambda p, _ctx: enum_value(p.get("ArmorSlot")),
    "Armor": field("Armor"),
    "Movement Speed Reduction": field("MovementSpeedReduction"),
    "Skill Requirements": lambda p, _ctx: required_skill_value(
        p.get("SkillRequirements")
    ),
}
