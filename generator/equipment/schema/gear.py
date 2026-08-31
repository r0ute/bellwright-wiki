from __future__ import annotations

from generator.equipment.schema.common import (
    FieldExtractor,
    field,
    required_skill_value,
    tier,
)

EQUIPMENT_FIELDS: dict[str, FieldExtractor] = {
    "Icon": lambda _p, ctx: ctx["icon"],
    "Name": lambda _p, ctx: ctx["name"],
    "Tier": tier,
    "Movement Speed Reduction": field("MovementSpeedReduction"),
    "Movement Acceleration Reduction": field("MovementAccelerationReduction"),
    "Skill Requirements": lambda p, _ctx: required_skill_value(
        p.get("SkillRequirements")
    ),
}
