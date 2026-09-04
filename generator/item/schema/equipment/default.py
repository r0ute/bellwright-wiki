from __future__ import annotations
from .common import FieldExtractor, context_field, field, tier

EQUIPMENT_FIELDS: dict[str, FieldExtractor] = {
    "Icon": context_field("icon"),
    "Name": field("Name"),
    "Category": field("Category"),
    "Tier": tier,
}
