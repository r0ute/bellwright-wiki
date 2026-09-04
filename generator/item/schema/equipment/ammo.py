from __future__ import annotations

from ..common import (
    FieldExtractor,
    asset_reference_name,
    context_field,
    field,
    nested_field,
    tier,
)

FIELDS: dict[str, FieldExtractor] = {
    "Icon": context_field("icon"),
    "Name": field("Name"),
    "Description": field("Description"),
    "Category": context_field("category"),
    "Rarity": field("Rarity", transform=asset_reference_name),
    "Tier": tier,
    "Max Stack Size": field("MaxStackSize"),
    "Expected Price": field("ExpectedPrice"),
    "Acquisition Hint": field("AcquisitionHint"),
    "Crafting XP": field("ExperienceRewardCrafting"),
    "Damage Type": field("DamageType", transform=asset_reference_name),
    "Damage": field("Damage"),
    "Projectile Damage": nested_field("ProjectileDamage", "Damage"),
    "Broken Version": context_field("damaged_item"),
}
EQUIPMENT_FIELDS = FIELDS
