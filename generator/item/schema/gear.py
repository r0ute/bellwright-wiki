from .common import (
    FieldExtractor,
    asset_reference_name,
    context_field,
    field,
    required_skill_value,
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
    "Max Durability": field("MaxDurability"),
    "Movement Speed Reduction": field("MovementSpeedReduction"),
    "Movement Acceleration Reduction": field("MovementAccelerationReduction"),
    "Skill Requirements": field("SkillRequirements", transform=required_skill_value),
    "Broken Version": context_field("damaged_item"),
}
