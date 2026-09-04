from __future__ import annotations

import json
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from ..discover import discover_json
from .category import CategoryIndex
from .classifier import (
    classify_item_family,
    family_for_path,
    is_generated_family,
)
from .model import Item


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


def _game_object_path(value: Any) -> str:
    """Extract a /Game/... object path from an Unreal reference."""
    if not isinstance(value, dict):
        return ""

    for key in ("ObjectPath", "AssetPathName", "ObjectName"):
        reference = value.get(key)

        if not isinstance(reference, str) or not reference:
            continue

        match = re.search(r"(/Game/[^']+)", reference)
        if match:
            return match.group(1)

        match = re.search(r"'([^']+)'", reference)
        if match:
            return match.group(1)

        if reference.startswith("/Game/"):
            return reference

    return ""


def _path_from_game_object(
    assets_root: Path,
    object_path: str,
) -> Path | None:
    """
    Convert an Unreal /Game/... asset reference into an FModel JSON path.

    Example:
        /Game/Mist/Data/Items/Fishes/BaseFish.0
    becomes:
        <assets_root>/Bellwright/Content/Mist/Data/Items/Fishes/BaseFish.json
    """
    if not object_path.startswith("/Game/"):
        return None

    path = object_path.split(".", 1)[0]

    relative = path.removeprefix("/Game/")

    candidate = assets_root / "Bellwright" / "Content" / f"{relative}.json"

    return candidate if candidate.exists() else None


def _category_from_template(
    path: Path,
    properties: dict[str, Any],
    category_index: CategoryIndex,
    assets_root: Path,
) -> str | None:
    """
    Resolve Category through inherited Unreal item templates.

    Many item subclasses do not repeat inherited properties in their
    exported CDO. For example, BeardedMullet derives from BaseFish_C,
    while BaseFish defines Category = Resources.

    Follow Template references until a Category is found.
    """
    direct = category_index.get_category(properties.get("Category"))

    if direct:
        return direct

    current_path = path
    visited: set[Path] = set()

    while current_path not in visited:
        visited.add(current_path)

        cdo = load_cdo(current_path)

        current_properties = cdo.get("Properties")
        if not isinstance(current_properties, dict):
            return None

        category = category_index.get_category(current_properties.get("Category"))
        if category:
            return category

        template = cdo.get("Template")
        template_path = _game_object_path(template)

        if not template_path:
            return None

        next_path = _path_from_game_object(
            assets_root,
            template_path,
        )

        if next_path is None:
            return None

        current_path = next_path

    return None


def discover_paths(assets_root: Path) -> Iterator[Path]:
    """Yield JSONs belonging to generated item source families."""
    for path in discover_json(assets_root):
        family = family_for_path(path)

        if is_generated_family(family):
            yield path


def discover_items(
    assets_root: Path,
    category_index: CategoryIndex,
) -> Iterator[Item]:
    """
    Discover actual item CDOs and classify them by semantic category.

    Category is resolved from the item's own Properties first, then
    inherited through its Unreal Template chain. The physical
    Items/<Family>/ directory remains only the fallback family.

    This is important for subclasses such as:

        Fishes/RaidMap/BeardedMullet.json
            -> Template BaseFish_C
            -> BaseFish.json
            -> Category Resources

    It also handles inherited categories for other item families.
    """
    for path in discover_paths(assets_root):
        cdo = load_cdo(path)

        properties = cdo.get("Properties")

        if not isinstance(properties, dict):
            continue

        name = _string_value(properties.get("Name"))

        if not name:
            continue

        source_family = family_for_path(path)

        if source_family is None:
            continue

        category = (
            _category_from_template(
                path,
                properties,
                category_index,
                assets_root,
            )
            or "Uncategorized"
        )

        family = classify_item_family(
            path,
            category,
            category_index=category_index,
        )

        if family is None:
            continue

        yield Item(
            path=path,
            family=family,
            template=superstruct_name(cdo),
            category=category,
            name=name,
            properties=properties,
        )


def load_broken_relationships(
    assets_root: Path,
) -> dict[str, tuple[str, str]]:
    """
    Index BrokenItems without treating them as generated item rows.
    """
    relationships: dict[str, tuple[str, str]] = {}

    for path in discover_json(assets_root):
        if family_for_path(path) != "BrokenItems":
            continue

        properties = load_properties(path)

        damaged = _reference_name(properties.get("DamagedItem"))
        parent = _reference_name(properties.get("UnbrokenParentItem"))

        if damaged or parent:
            relationships[path.stem] = (
                damaged,
                parent,
            )

    return relationships


def _reference_name(value: Any) -> str:
    if isinstance(value, dict):
        for key in (
            "ObjectPath",
            "AssetPathName",
            "ObjectName",
        ):
            candidate = value.get(key)

            if isinstance(candidate, str):
                value = candidate
                break

    if not isinstance(value, str):
        return ""

    value = value.rsplit("/", 1)[-1].split(".", 1)[0]

    value = value.rsplit("'", 1)[-1]

    return value.removesuffix("_C")
