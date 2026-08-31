from __future__ import annotations

from .common import (
    FieldExtractor,
    context_field,
    field,
    required_skill_value,
    tier,
)

EQUIPMENT_FIELDS: dict[str, FieldExtractor] = {
    "Icon": context_field("icon"),
    "Name": field("Name"),
    "Tier": tier,
    "Movement Speed Reduction": field("MovementSpeedReduction"),
    "Movement Acceleration Reduction": field("MovementAccelerationReduction"),
    "Skill Requirements": field(
        "SkillRequirements",
        transform=required_skill_value,
    ),
}
