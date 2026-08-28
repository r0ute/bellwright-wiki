from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

FieldExtractor = Callable[[dict[str, Any], dict[str, Any]], Any]


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
        "ObjectName",
    ):
        candidate = value.get(candidate_key)
        if candidate not in (None, ""):
            return candidate

    return None


def required_skill_value(properties: dict[str, Any], skill_name: str) -> Any:
    requirements = get_value(properties, "SkillRequirements",)

    if not isinstance(requirements, list):
        return "—"

    for requirement in requirements:
        if not isinstance(requirement, dict):
            continue

        key = str(requirement.get("Key", ""))
        if skill_name.lower() in key.lower():
            value = requirement.get("Value")
            return value if value is not None else "—"

    return "—"


def resolve_path_name(asset_path: str | None) -> str:
    if not asset_path:
        return "—"

    return Path(asset_path.split(".")[0]).name


def field(key: str, fallback: str = "—") -> FieldExtractor:
    def _extract(properties: dict[str, Any], _context: dict[str, Any]) -> Any:
        return extract_value(properties, key) or fallback

    return _extract