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
)


# ---------------------------------------------------------------------------
# Generic extraction
# ---------------------------------------------------------------------------


def extract_value(properties: dict[str, Any], key: str) -> Any:
    """Extract a scalar value from a FModel property."""
    value = properties.get(key)

    if not isinstance(value, dict):
        return value

    for candidate_key in VALUE_KEYS:
        candidate = value.get(candidate_key)
        if candidate not in (None, ""):
            return candidate

    return None


def nested_value(
    properties: dict[str, Any],
    keys: tuple[str, ...],
    fallback: Any = "",
) -> Any:
    """Extract a value from nested FModel property dictionaries."""
    value: Any = properties

    for key in keys:
        if not isinstance(value, dict):
            return fallback

        value = value.get(key)

    return fallback if value is None else value


# ---------------------------------------------------------------------------
# Value normalization
# ---------------------------------------------------------------------------


def asset_name(value: Any) -> str:
    """Extract an Unreal asset name from a string reference."""
    if not isinstance(value, str):
        return ""

    return value.rsplit("'", 1)[-1].removesuffix("_C")


def asset_reference_name(value: Any) -> str:
    """Extract a normalized name from an Unreal asset reference."""
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
    """Extract the final value from an Unreal enum reference."""
    if not isinstance(value, str):
        return ""

    return value.rsplit("::", 1)[-1]


def required_skill_value(requirements: Any) -> str:
    """Format skill requirements as a comma-separated string."""
    if not isinstance(requirements, list):
        return ""

    values = [
        f"{skill}: {value}"
        for requirement in requirements
        if isinstance(requirement, dict)
        for key, skill, value in [
            (
                str(requirement.get("Key", "")),
                str(requirement.get("Key", "")).rsplit("::", 1)[-1],
                requirement.get("Value"),
            )
        ]
        if skill and value is not None
    ]

    return ", ".join(values)


# ---------------------------------------------------------------------------
# Field extractors
# ---------------------------------------------------------------------------


def field(
    key: str,
    fallback: str = "",
    transform: ValueTransformer | None = None,
) -> FieldExtractor:
    """
    Create an extractor for a property.

    Without a transform, the property is passed through extract_value().
    With a transform, the raw property value is passed to the transformer.
    """

    def _extract(
        properties: dict[str, Any],
        _context: dict[str, Any],
    ) -> Any:
        if transform:
            return transform(properties.get(key))

        return extract_value(properties, key) or fallback

    return _extract


def nested_field(
    *keys: str,
    fallback: str = "",
) -> FieldExtractor:
    """Create an extractor for a nested property."""
    return lambda properties, _context: nested_value(properties, keys, fallback)


def context_field(key: str) -> FieldExtractor:
    """Create an extractor for a value supplied by the generation context."""
    return lambda _properties, context: context[key]


def tier(
    properties: dict[str, Any],
    context: dict[str, Any],
) -> Any:
    """Read Tier from the property, falling back to the asset path."""
    value = properties.get("Tier")
    if value is not None:
        return value

    parts = str(context["path"]).replace("\\", "/").split("/")

    for part in parts:
        if part.startswith("Tier") and part[4:].isdigit():
            return int(part[4:])

    return ""
