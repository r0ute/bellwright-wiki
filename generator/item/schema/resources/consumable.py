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
    "Nutrition Duration (hours)": field("NutritionDurationHours"),
    "Health Bonus": field("HealthBonus"),
    "Health Regen": field("HealthRegen"),
    "Stamina Bonus": field("StaminaBonus"),
    "Stamina Regen": field("StaminaRegen"),
    "Food Type": field("FoodType", transform=enum_value),
    "Spoilage": field("bEnableSpoilage"),
    "Broken Version": context_field("damaged_item"),
}
CONSUMABLE_FIELDS = FIELDS
