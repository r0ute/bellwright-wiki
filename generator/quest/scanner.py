"""Discover root quests and resolve their ordered subquests."""

import json
import re
from pathlib import Path

from ..discover import discover_json
from .model import Quest, QuestStep


def _load_objects(path: Path) -> list[dict]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
    ):
        return []

    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]

    if isinstance(value, dict):
        objects = value.get("Objects")

        if isinstance(objects, list):
            return [item for item in objects if isinstance(item, dict)]

        return [value]

    return []


def _object_name(obj: dict) -> str:
    value = obj.get("Name")
    return value.strip() if isinstance(value, str) else ""


def _usable_object_name(value: str) -> str:
    if not value or value.startswith("Default__"):
        return ""

    value = re.sub(r"_C$", "", value)

    return value.strip()


def _is_quest_object(obj: dict) -> bool:
    value = obj.get("Type")

    if not isinstance(value, str):
        return False

    return "quest" in value.casefold()


def _quest_object(objects: list[dict]) -> dict | None:
    for obj in objects:
        if _is_quest_object(obj):
            return obj

    return None


def _properties(obj: dict) -> dict:
    value = obj.get("Properties")

    return value if isinstance(value, dict) else {}


def _text(value) -> str:
    if isinstance(value, str):
        return value.strip()

    if isinstance(value, dict):
        for key in (
            "SourceString",
            "LocalizedString",
            "StringTableEntry",
            "Value",
            "Text",
        ):
            result = _text(value.get(key))

            if result:
                return result

    return ""


def _title(obj: dict) -> str:
    return _text(_properties(obj).get("Title"))


def _summary(obj: dict) -> str:
    return _text(_properties(obj).get("Summary"))


def _class_name(value) -> str:
    if not isinstance(value, dict):
        return ""

    object_name = value.get("ObjectName")

    if not isinstance(object_name, str):
        return ""

    match = re.search(
        r"BlueprintGeneratedClass'([^']+)'",
        object_name,
    )

    if not match:
        return ""

    return _usable_object_name(match.group(1))


def _subquest_names(
    obj: dict,
) -> list[tuple[str, bool]]:
    subquests = _properties(obj).get("Subquests")

    if not isinstance(subquests, list):
        return []

    result = []

    for subquest in subquests:
        if not isinstance(subquest, dict):
            continue

        name = _class_name(subquest.get("QuestClass"))

        if not name:
            continue

        result.append(
            (
                name,
                bool(
                    subquest.get(
                        "bGroupNext",
                        False,
                    )
                ),
            )
        )

    return result


def _resolve_step_files(
    directory: Path,
    subquests: list[tuple[str, bool]],
) -> tuple[QuestStep, ...]:
    files: dict[str, Path] = {}

    for path in directory.glob("*.json"):
        objects = _load_objects(path)

        for obj in objects:
            name = _usable_object_name(_object_name(obj))

            if name:
                files[name] = path
                break

    steps = []

    for name, group_next in subquests:
        source = files.get(name)

        if source is None:
            continue

        objects = _load_objects(source)

        quest_object = None

        for obj in objects:
            object_name = _usable_object_name(_object_name(obj))

            if object_name == name:
                quest_object = obj
                break

        if quest_object is None:
            continue

        steps.append(
            QuestStep(
                name=name,
                source=source,
                summary=_summary(quest_object),
                group_next=group_next,
            )
        )

    return tuple(steps)


def _category(
    relative: Path,
    categories: dict[str, str],
) -> tuple[str, str] | None:
    configured = {name.casefold(): (name, slug) for name, slug in categories.items()}

    for part in relative.parts:
        result = configured.get(part.casefold())

        if result:
            return result

    return None


def _relative_tree_path(
    relative: Path,
    category: str,
) -> tuple[str, ...]:
    parts = list(relative.parts)

    category_index = next(
        index
        for index, part in enumerate(parts)
        if part.casefold() == category.casefold()
    )

    return tuple(parts[category_index + 1 : -1])


def _is_root_quest(
    objects: list[dict],
) -> bool:
    obj = _quest_object(objects)

    if obj is None:
        return False

    return isinstance(
        _properties(obj).get("Subquests"),
        list,
    )


def discover_quests(
    assets: Path,
    categories: dict[str, str],
) -> dict[str, list[Quest]]:
    result = {category: [] for category in categories}

    for path in discover_json(assets):
        try:
            relative = path.relative_to(assets)
        except ValueError:
            continue

        category = _category(
            relative,
            categories,
        )

        if category is None:
            continue

        objects = _load_objects(path)

        if not _is_root_quest(objects):
            continue

        quest_object = _quest_object(objects)

        if quest_object is None:
            continue

        category_name, _ = category

        name = _usable_object_name(_object_name(quest_object))

        if not name:
            name = path.stem

        subquests = _subquest_names(quest_object)

        steps = _resolve_step_files(
            path.parent,
            subquests,
        )

        result[category_name].append(
            Quest(
                name=name,
                category=category_name,
                source=path,
                relative_path=_relative_tree_path(
                    relative,
                    category_name,
                ),
                title=_title(quest_object) or name,
                summary=_summary(quest_object),
                steps=steps,
            )
        )

    for quests in result.values():
        quests.sort(
            key=lambda quest: (
                tuple(part.casefold() for part in quest.relative_path),
                quest.title.casefold(),
                quest.name.casefold(),
                quest.source.as_posix().casefold(),
            )
        )

    return result
