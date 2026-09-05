from __future__ import annotations

from importlib import import_module
from typing import Any

CATEGORY_SCHEMAS = {
    "Ammo": "ammo",
    "Ammo_Arrows": "ammo",
    "Ammo_Bolts": "ammo",
    "Armors": "armors",
    "HeavyArmors": "armors",
    "MediumArmors": "armors",
    "Clothing": "clothing",
    "Gear": "gear",
    "Shields": "gear",
    "Medicine": "healing",
    "Tools": "tools",
    "Weapons": "weapons",
    "OneHanded": "weapons",
    "TwoHanded": "weapons",
    "Bows": "weapons",
    "FoodRation": "consumable",
    "BakedFood": "consumable",
    "CookedFood": "consumable",
    "DriedFood": "consumable",
    "OvercookedFood": "consumable",
    "PreservedFood": "consumable",
    "RawFood": "consumable",
    "SoupFood": "consumable",
    "StewFood": "consumable",
    "Seeds": "seed",
    "Decorations": "placeable_decorations",
    "QuestItem": "unique_quest_items",
}

TEMPLATE_SCHEMAS = {
    "BaseFish": "fishes",
    "Base_FishingLootContainer": "fishes",
}


def schema_module(index: Any, category_node: Any, template: str):
    class_name = getattr(category_node, "class_name", "")
    module_name = CATEGORY_SCHEMAS.get(class_name)
    if module_name:
        return import_module(f"generator.item.schema.{module_name}")
    module_name = TEMPLATE_SCHEMAS.get(template)
    if module_name:
        return import_module(f"generator.item.schema.{module_name}")
    return import_module("generator.item.schema.default")
