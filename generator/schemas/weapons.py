from collections.abc import Callable
from pathlib import Path


FieldExtractor = Callable[[dict, dict], object]


def value(properties: dict, key: str):
    value = properties.get(key)

    if isinstance(value, dict):
        return (
            value.get("LocalizedString")
            or value.get("SourceString")
            or value.get("AssetPathName")
            or value.get("ObjectName")
        )

    return value


def weapon_type(properties: dict):
    weapon_type = properties.get("WeaponType")

    if isinstance(weapon_type, dict):
        asset_path = weapon_type.get("AssetPathName", "")

        if asset_path:
            return Path(asset_path.split(".")[0]).name

        return weapon_type.get("ObjectName", "—")

    return weapon_type or "—"


def weapon_strength(properties: dict):
    requirements = properties.get("SkillRequirements", [])

    if not isinstance(requirements, list):
        return "—"

    for requirement in requirements:
        if not isinstance(requirement, dict):
            continue

        if "Strength" in str(requirement.get("Key", "")):
            return requirement.get("Value", "—")

    return "—"


def durability(properties: dict, _context: dict):
    return (
        value(properties, "MaxDurability")
        or value(properties, "Durability")
        or "—"
    )


def price(properties: dict, _context: dict):
    return (
        value(properties, "ExpectedPrice")
        or value(properties, "Price")
        or "—"
    )


WEAPON_FIELDS: dict[str, FieldExtractor] = {
    "Icon": lambda _p, context: context["icon"],
    "Name": lambda _p, context: context["name"],
    "Type": lambda p, _c: weapon_type(p),
    "Tier": lambda p, _c: value(p, "Tier") or "—",
    "Damage": lambda p, _c: value(p, "Damage") or "—",
    "Thrust": lambda p, _c: value(p, "ThrustDamage") or "—",
    "Speed": lambda p, _c: value(p, "WeaponSpeed") or "—",
    "Impact": lambda p, _c: value(p, "Impact") or "—",
    "Stability": lambda p, _c: value(p, "Stability") or "—",
    "Length": lambda p, _c: value(p, "WeaponLength") or "—",
    "Max Durability": durability,
    "Price": price,
    "Strength": lambda p, _c: weapon_strength(p),
}