"""Discover and filter quest assets."""

import json
import re
from pathlib import Path

from ..discover import discover_json
from .constants import QUEST_CATEGORIES
from .models import Quest


def _load_objects(path: Path) -> list[dict]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return []

    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]

    if isinstance(value, dict):
        objects = value.get("Objects")
        if isinstance(objects, list):
            return [item for item in objects if isinstance(item, dict)]
        return [value]

    return []


def _is_quest_object(obj: dict) -> bool:
    object_type = obj.get("Type")
    return isinstance(object_type, str) and "quest" in object_type.casefold()


def _text(value) -> str:
    if isinstance(value, str):
        return value.strip()

    if isinstance(value, dict):
        for key in (
            "SourceString",
            "StringTableEntry",
            "LocalizedString",
            "Value",
            "Text",
        ):
            result = _text(value.get(key))
            if result:
                return result

    return ""


def _property_name(obj: dict) -> str:
    properties = obj.get("Properties")
    if not isinstance(properties, dict):
        return ""

    for key in ("QuestName", "DisplayName", "Title", "Name"):
        value = _text(properties.get(key))
        if value:
            return value

    return ""


def _object_name(obj: dict) -> str:
    value = obj.get("Name")
    return value.strip() if isinstance(value, str) else ""


def _usable_object_name(value: str) -> str:
    if not value or value.startswith("Default__"):
        return ""

    value = re.sub(r"_C$", "", value)
    return value.strip()


def _quest_name(path: Path, objects: list[dict]) -> str:
    for obj in objects:
        if not _is_quest_object(obj):
            continue

        value = _property_name(obj)
        if value:
            return value

    for obj in objects:
        if not _is_quest_object(obj):
            continue

        value = _usable_object_name(_object_name(obj))
        if value:
            return value

    return path.stem


def _category(relative: Path) -> tuple[str, str] | None:
    configured = {
        name.casefold(): (name, slug) for name, slug in QUEST_CATEGORIES.items()
    }

    for part in relative.parts:
        result = configured.get(part.casefold())
        if result:
            return result

    return None


def _relative_tree_path(relative: Path, category: str) -> tuple[str, ...]:
    parts = list(relative.parts)
    category_index = next(
        index
        for index, part in enumerate(parts)
        if part.casefold() == category.casefold()
    )

    # JSON filename is the quest asset; everything before it is its
    # source hierarchy below MainQuest/SideQuests.
    return tuple(parts[category_index + 1 : -1])


def discover_quests(assets: Path) -> dict[str, list[Quest]]:
    """Discover quests only inside configured quest categories."""
    result = {category: [] for category in QUEST_CATEGORIES}

    for path in discover_json(assets):
        try:
            relative = path.relative_to(assets)
        except ValueError:
            continue

        category = _category(relative)
        if category is None:
            continue

        objects = _load_objects(path)
        if not any(_is_quest_object(obj) for obj in objects):
            continue

        category_name, _ = category
        result[category_name].append(
            Quest(
                name=_quest_name(path, objects),
                category=category_name,
                source=path,
                relative_path=_relative_tree_path(relative, category_name),
            )
        )

    for quests in result.values():
        quests.sort(
            key=lambda quest: (
                tuple(part.casefold() for part in quest.relative_path),
                quest.name.casefold(),
                quest.source.as_posix().casefold(),
            )
        )

    return result
