from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

FieldExtractor = Callable[[dict[str, Any], dict[str, Any]], Any]

DAMAGE_TYPES = ("Piercing",)


def get_value(properties: dict[str, Any], key: str) -> Any:
    return properties.get(key)


def extract_value(properties: dict[str, Any], key: str) -> Any:
    value = get_value(properties, key)

    if not isinstance(value, dict):
        return value

    for candidate_key in (
        "LocalizedString",
        "SourceString",
        "AssetPathName",
        "ObjectPath",
        "ObjectName",
    ):
        candidate = value.get(candidate_key)
        if candidate not in (None, ""):
            return candidate

    return None


def asset_name(value: Any) -> str:
    if not isinstance(value, str):
        return ""

    return value.rsplit("'", 1)[-1].removesuffix("_C")


def asset_reference_name(value: Any) -> str:
    if isinstance(value, dict):
        value = (
            value.get("ObjectPath")
            or value.get("AssetPathName")
            or value.get("ObjectName")
        )

    if not isinstance(value, str) or not value:
        return ""

    if value.startswith("/Game/"):
        value = value.rsplit("/", 1)[-1].split(".", 1)[0]
    else:
        value = value.rsplit("'", 1)[-1]

    return value.removesuffix("_C")


def required_skill_value(
    properties: dict[str, Any],
    skill_name: str,
) -> Any:
    requirements = get_value(properties, "SkillRequirements")

    if not isinstance(requirements, list):
        return ""

    for requirement in requirements:
        if not isinstance(requirement, dict):
            continue

        key = str(requirement.get("Key", ""))

        if skill_name.lower() in key.lower():
            value = requirement.get("Value")
            return value if value is not None else ""

    return ""


def damage_type(
    properties: dict[str, Any],
    _context: dict[str, Any],
) -> str:
    name = asset_reference_name(properties.get("DamageType"))

    for damage in DAMAGE_TYPES:
        if damage.lower() in name.lower():
            return damage

    return ""


def resolve_path_name(value: Any) -> str:
    if isinstance(value, dict):
        value = (
            value.get("AssetPathName")
            or value.get("ObjectPath")
            or value.get("ObjectName")
        )

    if not isinstance(value, str) or not value:
        return ""

    return Path(value.split(".", 1)[0]).name


def nested_field(
    *keys: str,
    fallback: str = "",
) -> FieldExtractor:
    def _extract(
        properties: dict[str, Any],
        _context: dict[str, Any],
    ) -> Any:
        value: Any = properties

        for key in keys:
            if not isinstance(value, dict):
                return fallback

            value = value.get(key)

        return value if value is not None else fallback

    return _extract


def field(
    key: str,
    fallback: str = "",
) -> FieldExtractor:
    def _extract(
        properties: dict[str, Any],
        _context: dict[str, Any],
    ) -> Any:
        return extract_value(properties, key) or fallback

    return _extract
