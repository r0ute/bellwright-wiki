from __future__ import annotations
from typing import Any
try:
    from generator.schemas.common import (
        FieldExtractor,
        extract_value,
        field,
    )
except ModuleNotFoundError:
    from schemas.common import (
        FieldExtractor,
        extract_value,
        field,
    )

EQUIPMENT_FIELDS: dict[str, FieldExtractor] = {
    "Icon": lambda _p, ctx: ctx['icon'],
    "Name": lambda _p, ctx: ctx['name'],
    "Category": field('Category'),
    "Price": field('ExpectedPrice'),
}
