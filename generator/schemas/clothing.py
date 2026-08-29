from __future__ import annotations

from generator.schemas.common import (
    FieldExtractor,
    enum_value,
    field,
    required_skill_value,
)

EQUIPMENT_FIELDS: dict[str, FieldExtractor] = {
    "B Repairable": field("bRepairable"),
    "Codex Entry": field("CodexEntry"),
    "B Ignore Container Max Stack Size": field("bIgnoreContainerMaxStackSize"),
    "Icon": lambda _p, ctx: ctx["icon"],
    "Name": lambda _p, ctx: ctx["name"],
    "Armor Slot": lambda p, _ctx: enum_value(p.get("ArmorSlot")),
    "Armor": field("Armor"),
    "MovementSpeedReduction": field("MovementSpeedReduction"),
    "SkillRequirements": lambda p, _ctx: required_skill_value(
        p.get("SkillRequirements")
    ),
}
