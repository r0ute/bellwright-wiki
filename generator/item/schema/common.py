from __future__ import annotations

from collections.abc import Callable
from typing import Any

FieldExtractor = Callable[[dict[str, Any], dict[str, Any]], Any]
ValueTransformer = Callable[[Any], Any]

ASSET_REFERENCE_KEYS = ("ObjectPath", "AssetPathName", "ObjectName")
VALUE_KEYS = (
    "LocalizedString",
    "SourceString",
    "AssetPathName",
    "ObjectPath",
    "ObjectName",
    "Value",
)


def extract_value(properties: dict[str, Any], key: str) -> Any:
    value = properties.get(key)
    if not isinstance(value, dict):
        return value
    for candidate_key in VALUE_KEYS:
        candidate = value.get(candidate_key)
        if candidate not in (None, ""):
            return candidate
    return None


def asset_reference_name(value: Any) -> str:
    if isinstance(value, dict):
        value = next(
            (value.get(key) for key in ASSET_REFERENCE_KEYS if value.get(key)),
            None,
        )
    if not isinstance(value, str) or not value:
        return ""
    if value.startswith("/Game/"):
        value = value.rsplit("/", 1)[-1].split(".", 1)[0]
    else:
        value = value.rsplit("'", 1)[-1]
    return value.removesuffix("_C")


def enum_value(value: Any) -> str:
    return value.rsplit("::", 1)[-1] if isinstance(value, str) else ""


def required_skill_value(requirements: Any) -> str:
    if not isinstance(requirements, list):
        return ""
    values = [
        f"{skill}: {value}"
        for requirement in requirements
        if isinstance(requirement, dict)
        for skill, value in [
            (
                str(requirement.get("Key", "")).rsplit("::", 1)[-1],
                requirement.get("Value"),
            )
        ]
        if skill and value is not None
    ]
    return ", ".join(values)


def field(
    key: str,
    fallback: str = "",
    transform: ValueTransformer | None = None,
) -> FieldExtractor:
    def _extract(properties: dict[str, Any], _context: dict[str, Any]) -> Any:
        value = properties.get(key)
        if transform:
            return transform(value)
        value = extract_value(properties, key)
        return fallback if value is None else value

    return _extract


def nested_field(*keys: str, fallback: str = "") -> FieldExtractor:
    def _extract(properties: dict[str, Any], _context: dict[str, Any]) -> Any:
        value: Any = properties
        for key in keys:
            if not isinstance(value, dict):
                return fallback
            value = value.get(key)
        return fallback if value is None else value

    return _extract


def context_field(key: str) -> FieldExtractor:
    return lambda _properties, context: context.get(key, "")


def tier(properties: dict[str, Any], context: dict[str, Any]) -> Any:
    value = properties.get("Tier")
    if value is not None:
        return value
    parts = str(context.get("path", "")).replace("\\", "/").split("/")
    for part in parts:
        if part.startswith("Tier") and part[4:].isdigit():
            return int(part[4:])
    return ""
