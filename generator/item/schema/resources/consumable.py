from .resource import FIELDS as RESOURCE_FIELDS
from ..common import FieldExtractor, field, enum_value

FIELDS: dict[str, FieldExtractor] = dict(RESOURCE_FIELDS)
FIELDS.update({
    "Nutrition Duration (hours)": field("NutritionDurationHours"),
    "Health Bonus": field("HealthBonus"),
    "Health Regen": field("HealthRegen"),
    "Stamina Bonus": field("StaminaBonus"),
    "Stamina Regen": field("StaminaRegen"),
    "Food Type": field("FoodType", transform=enum_value),
    "Spoilage": field("bEnableSpoilage"),
})
CONSUMABLE_FIELDS = FIELDS
