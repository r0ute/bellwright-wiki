from __future__ import annotations

from generator.schema.common import (
    FieldExtractor,
    field,
    tier,
)

EQUIPMENT_FIELDS: dict[str, FieldExtractor] = {
    "Icon": lambda _p, ctx: ctx["icon"],
    "Name": lambda _p, ctx: ctx["name"],
    "Category": field("Category"),
    "Tier": tier,
}
