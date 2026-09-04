from __future__ import annotations

from ..common import FieldExtractor, asset_reference_name, context_field, enum_value, field, tier

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
    "Volume": field("Volume"),
    "Mesh": field("Mesh"),
    "Carry Animation": field("CarryAnimTypeOverride"),
    "Animal Class": field("AnimalClass", transform=enum_value),
    "Broken Version": context_field("damaged_item"),
}
CARCASS_FIELDS = FIELDS
