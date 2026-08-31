"""Discover root quests and resolve their ordered subquests."""

from pathlib import Path

from ..discover import discover_json
from .model import Quest
from .parser import ObjectIndex, parse_quest
from .reader import read_objects


def _category(
    relative: Path,
    categories: set[str],
) -> str | None:
    configured = {name.casefold(): name for name in categories}

    for part in relative.parts:
        category = configured.get(part.casefold())

        if category:
            return category

    return None


def _index_objects(
    paths: list[Path],
) -> dict[Path, ObjectIndex]:
    indexes: dict[Path, ObjectIndex] = {}

    for path in paths:
        objects = read_objects(path)

        for obj in objects:
            name = obj.get("Name")

            if not isinstance(name, str):
                continue

            name = name.strip()

            if not name or name.startswith("Default__"):
                continue

            if name.endswith("_C"):
                name = name[:-2]

            name = name.strip()

            if not name:
                continue

            indexes.setdefault(
                path.parent,
                {},
            )[name] = (
                path,
                objects,
            )

            break

    return indexes


def _sort_quests(
    quests_by_category: dict[str, list[Quest]],
) -> None:
    for quests in quests_by_category.values():
        quests.sort(
            key=lambda quest: (
                tuple(part.casefold() for part in quest.relative_path),
                quest.title.casefold(),
                quest.name.casefold(),
                quest.source.as_posix().casefold(),
            )
        )


def discover_quests(
    assets: Path,
    categories: set[str],
) -> dict[str, list[Quest]]:
    """Discover quests belonging to configured categories."""
    quests_by_category = {category: [] for category in categories}

    paths = list(discover_json(assets))
    directory_indexes = _index_objects(paths)

    for path in paths:
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

        objects = read_objects(path)

        quest = parse_quest(
            path=path,
            relative_path=relative,
            category=category,
            objects=objects,
            directory_objects=directory_indexes.get(
                path.parent,
                {},
            ),
        )

        if quest is not None:
            quests_by_category[category].append(quest)

    _sort_quests(quests_by_category)

    return quests_by_category
