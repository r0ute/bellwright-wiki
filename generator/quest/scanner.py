"""Discover root quests and resolve their ordered subquests."""

import json
from pathlib import Path

from ..discover import discover_json
from .model import Quest, QuestItem, QuestStep


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

    if value.endswith("_C"):
        value = value[:-2]

    return value.strip()


def _is_quest_object(obj: dict) -> bool:
    value = obj.get("Type")

    if not isinstance(value, str):
        return False

    return "quest" in value.casefold()


def _quest_object(
    objects: list[dict],
) -> dict | None:
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


def _description(obj: dict) -> str:
    properties = _properties(obj)

    for key, value in properties.items():
        if key.casefold().endswith("taskdescription"):
            text = _text(value)

            if text:
                return text

    return _text(properties.get("Description"))


def _class_name(value) -> str:
    if not isinstance(value, dict):
        return ""

    object_name = value.get("ObjectName")

    if not isinstance(object_name, str):
        return ""

    start = object_name.find("'")
    end = object_name.rfind("'")

    if start == -1 or end <= start:
        return ""

    return _usable_object_name(object_name[start + 1 : end])


def _integer(value, default: int = 0) -> int:
    if isinstance(value, bool):
        return default

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        return int(value)

    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return default

    return default


def _items(obj: dict) -> tuple[QuestItem, ...]:
    values = _properties(obj).get("Items")

    if not isinstance(values, list):
        return ()

    result = []

    for value in values:
        if not isinstance(value, dict):
            continue

        item_name = _class_name(value.get("ItemClass"))

        if not item_name:
            continue

        min_amount = _integer(value.get("MinAmount"))
        max_amount = _integer(
            value.get("MaxAmount"),
            min_amount,
        )

        result.append(
            QuestItem(
                name=item_name,
                min_amount=min_amount,
                max_amount=max_amount,
            )
        )

    return tuple(result)


def _subquests(
    obj: dict,
) -> list[tuple[str, str, bool]]:
    values = _properties(obj).get("Subquests")

    if not isinstance(values, list):
        return []

    result = []

    for value in values:
        if not isinstance(value, dict):
            continue

        name = _class_name(value.get("QuestClass"))

        if not name:
            continue

        quest_type = value.get("Type", "")

        if not isinstance(quest_type, str):
            quest_type = ""

        result.append(
            (
                name,
                quest_type,
                bool(
                    value.get(
                        "bGroupNext",
                        False,
                    )
                ),
            )
        )

    return result


def _split_words(value: str) -> list[str]:
    words = []
    word = ""

    for index, char in enumerate(value):
        previous = value[index - 1] if index else ""
        following = value[index + 1] if index + 1 < len(value) else ""

        boundary = (
            char == "_"
            or (word and char.isupper() and previous.islower())
            or (word and char.isupper() and previous.isupper() and following.islower())
        )

        if boundary:
            if word:
                words.append(word)
                word = ""

            if char == "_":
                continue

        word += char

    if word:
        words.append(word)

    return words


def _fallback_step_title(
    quest_name: str,
    step_name: str,
) -> str:
    name = step_name

    if name.startswith(f"{quest_name}_"):
        name = name[len(quest_name) + 1 :]
    elif name.startswith(quest_name):
        name = name[len(quest_name) :]

    name = name.lstrip("_")

    return " ".join(_split_words(name)).strip()


def _step_title(
    quest_name: str,
    quest_title: str,
    step_name: str,
    step_object: dict,
) -> str:
    title = _title(step_object)

    if title and title.casefold() != quest_title.casefold():
        return title

    return _fallback_step_title(
        quest_name,
        step_name,
    )


def _resolve_steps(
    directory: Path,
    quest_name: str,
    quest_title: str,
    subquests: list[tuple[str, str, bool]],
) -> tuple[QuestStep, ...]:
    files = {}

    for path in directory.glob("*.json"):
        objects = _load_objects(path)

        for obj in objects:
            name = _usable_object_name(_object_name(obj))

            if name:
                files[name] = (
                    path,
                    objects,
                )
                break

    steps = []

    for name, quest_type, group_next in subquests:
        entry = files.get(name)

        if entry is None:
            continue

        source, objects = entry
        step_object = _quest_object(objects)

        if step_object is None:
            continue

        steps.append(
            QuestStep(
                name=_step_title(
                    quest_name,
                    quest_title,
                    name,
                    step_object,
                ),
                source=source,
                summary=_description(step_object),
                type=quest_type,
                group_next=group_next,
                items=_items(step_object),
            )
        )

    return tuple(steps)


def _category(
    relative: Path,
    categories: dict[str, str],
) -> tuple[str, str] | None:
    configured = {
        name.casefold(): (
            name,
            name.lower(),
        )
        for name in categories
    }

    for part in relative.parts:
        result = configured.get(part.casefold())

        if result:
            return result

    return None


def _relative_tree_path(
    relative: Path,
    category: str,
) -> tuple[str, ...]:
    parts = relative.parts

    category_index = next(
        index
        for index, part in enumerate(parts)
        if part.casefold() == category.casefold()
    )

    return tuple(parts[category_index + 1 : -1])


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
        quest_object = _quest_object(objects)

        if quest_object is None:
            continue

        if not isinstance(
            _properties(quest_object).get("Subquests"),
            list,
        ):
            continue

        category_name, _ = category

        name = _usable_object_name(_object_name(quest_object))

        if not name:
            name = path.stem

        title = _title(quest_object) or name

        result[category_name].append(
            Quest(
                name=name,
                category=category_name,
                source=path,
                relative_path=_relative_tree_path(
                    relative,
                    category_name,
                ),
                title=title,
                summary=_summary(quest_object),
                steps=_resolve_steps(
                    path.parent,
                    name,
                    title,
                    _subquests(quest_object),
                ),
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
