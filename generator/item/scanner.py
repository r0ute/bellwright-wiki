from __future__ import annotations

import json
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from ..discover import discover_json
from .category import CategoryIndex
from .classifier import family_for_path
from .model import Item

ITEM_FAMILIES = {
    "Equipment",
    "Resources",
    "UniqueQuestItems",
    "PlaceableDecorations",
    "Special",
    "UniqueQuestItemsRaidMap",
    "Fishes",
    "Healing",
}


def load_objects(path: Path) -> list[dict]:
    """Load FModel JSON as a list of objects."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if isinstance(raw, list):
        return [obj for obj in raw if isinstance(obj, dict)]
    return [raw] if isinstance(raw, dict) else []


def find_cdo(objects: list[dict]) -> dict | None:
    """Return the first object containing a Properties mapping."""
    return next(
        (
            obj
            for obj in objects
            if isinstance(obj, dict) and isinstance(obj.get("Properties"), dict)
        ),
        None,
    )


def load_cdo(path: Path) -> dict:
    return find_cdo(load_objects(path)) or {}


def load_properties(path: Path) -> dict[str, Any]:
    cdo = load_cdo(path)
    properties = cdo.get("Properties")
    return properties if isinstance(properties, dict) else {}


def superstruct_name(cdo: dict) -> str:
    """Return the Unreal template class name from SuperStruct."""
    value = cdo.get("SuperStruct")
    if isinstance(value, dict):
        value = (
            value.get("ObjectName")
            or value.get("AssetPathName")
            or value.get("ObjectPath")
        )
    if not isinstance(value, str):
        return ""
    match = re.search(r"'([^']+)'", value)
    value = match.group(1) if match else value
    value = value.rsplit("/", 1)[-1].split(".", 1)[0]
    return value.removesuffix("_C")


def _string_value(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        for key in (
            "LocalizedString",
            "SourceString",
            "Value",
            "ObjectName",
            "AssetPathName",
            "ObjectPath",
        ):
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
    return ""


def discover_paths(assets_root: Path) -> Iterator[Path]:
    """Yield JSONs belonging to supported item families."""
    for path in discover_json(assets_root):
        if family_for_path(path) in ITEM_FAMILIES:
            yield path


def discover_items(
    assets_root: Path,
    category_index: CategoryIndex,
) -> Iterator[Item]:
    """Discover actual item CDOs, not every JSON beneath an item family."""
    for path in discover_paths(assets_root):
        cdo = load_cdo(path)
        properties = cdo.get("Properties")
        if not isinstance(properties, dict):
            continue

        name = _string_value(properties.get("Name"))
        if not name:
            continue

        family = family_for_path(path)
        if family is None:
            continue

        yield Item(
            path=path,
            family=family,
            template=superstruct_name(cdo),
            category=(
                category_index.get_category(properties.get("Category"))
                or "Uncategorized"
            ),
            name=name,
            properties=properties,
        )


def load_broken_relationships(
    assets_root: Path,
) -> dict[str, tuple[str, str]]:
    """Index BrokenItems without treating them as generated item rows."""
    relationships: dict[str, tuple[str, str]] = {}
    for path in discover_json(assets_root):
        if family_for_path(path) != "BrokenItems":
            continue
        properties = load_properties(path)
        damaged = _reference_name(properties.get("DamagedItem"))
        parent = _reference_name(properties.get("UnbrokenParentItem"))
        if damaged or parent:
            relationships[path.stem] = (damaged, parent)
    return relationships


def _reference_name(value: Any) -> str:
    if isinstance(value, dict):
        for key in ("ObjectPath", "AssetPathName", "ObjectName"):
            candidate = value.get(key)
            if isinstance(candidate, str):
                value = candidate
                break
    if not isinstance(value, str):
        return ""
    value = value.rsplit("/", 1)[-1].split(".", 1)[0]
    value = value.rsplit("'", 1)[-1]
    return value.removesuffix("_C")
