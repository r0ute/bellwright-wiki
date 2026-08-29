from __future__ import annotations

from typing import Any

try:
    from generator.schemas.common import (
        FieldExtractor,
        extract_value,
        field,
        required_skill_value,
        resolve_path_name,
    )
except ModuleNotFoundError:  # direct script execution
    from schemas.common import (
        FieldExtractor,
        extract_value,
        field,
        required_skill_value,
        resolve_path_name,
    )


def weapon_type(properties: dict[str, Any]) -> str:
    weapon_type = properties.get("WeaponType")

    if isinstance(weapon_type, dict):
        asset_path = weapon_type.get("AssetPathName")
        if asset_path:
            return resolve_path_name(asset_path)

        return weapon_type.get("ObjectName", "")

    return weapon_type or ""


def durability(properties: dict[str, Any], _context: dict[str, Any]) -> Any:
    return (
        extract_value(properties, "MaxDurability")
        or extract_value(properties, "Durability")
        or ""
    )


def price(properties: dict[str, Any], _context: dict[str, Any]) -> Any:
    return (
        extract_value(properties, "ExpectedPrice")
        or extract_value(properties, "Price")
        or ""
    )


def strength(properties: dict[str, Any], _context: dict[str, Any]) -> Any:
    return required_skill_value(properties, "Strength")


EQUIPMENT_FIELDS: dict[str, FieldExtractor] = {
    "Icon": lambda _properties, context: context["icon"],
    "Name": lambda _properties, context: context["name"],
    "Type": lambda properties, _context: weapon_type(properties),
    "Tier": field("Tier"),
    "Damage": field("Damage"),
    "Thrust": field("ThrustDamage"),
    "Speed": field("WeaponSpeed"),
    "Impact": field("Impact"),
    "Stability": field("Stability"),
    "Length": field("WeaponLength"),
    "Max Durability": durability,
    "Price": price,
    "Strength": strength,
}