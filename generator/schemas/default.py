from __future__ import annotations

from generator.schemas.common import (
    FieldExtractor,
    field,
)

EQUIPMENT_FIELDS: dict[str, FieldExtractor] = {
    "Icon": lambda _p, ctx: ctx["icon"],
    "Name": lambda _p, ctx: ctx["name"],
    "Category": field("Category"),
    "Price": field("ExpectedPrice"),
}
