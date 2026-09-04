from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ..discover import discover_json

CATEGORY_CLASSES = {
    "MistItemCategory",
    "MistItemCategory_C",
    "MistItemCategoryGroup",
    "MistItemCategoryGroup_C",
}

CATEGORY_GROUP_CLASSES = {
    "MistItemCategoryGroup",
    "MistItemCategoryGroup_C",
}


def _load_objects(path: Path) -> list[dict]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    if isinstance(raw, list):
        return [obj for obj in raw if isinstance(obj, dict)]

    return [raw] if isinstance(raw, dict) else []


def _superstruct_name(obj: dict) -> str:
    value = obj.get("SuperStruct")

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

    return value.rsplit("/", 1)[-1].split(".", 1)[0].removesuffix("_C")


def _property_name(obj: dict) -> str | None:
    properties = obj.get("Properties")

    if not isinstance(properties, dict):
        return None

    value = properties.get("Name")

    if isinstance(value, dict):
        value = value.get("LocalizedString") or value.get("SourceString")

    if isinstance(value, str) and value.strip():
        return value.strip()

    return None


def category_key_from_ref(value: Any) -> str | None:
    if not isinstance(value, dict):
        return None

    for key in ("ObjectPath", "AssetPathName", "ObjectName"):
        ref = value.get(key)

        if not isinstance(ref, str) or not ref:
            continue

        if ref.startswith("/Game/"):
            return ref.rsplit("/", 1)[-1].split(".", 1)[0]

        match = re.search(r"'([^']+)'", ref)
        if match:
            return match.group(1)

    return None


def normalize_category_key(value: str) -> str:
    value = value.strip()

    if value.endswith("_C"):
        value = value[:-2]

    return re.sub(r"[^a-z0-9]", "", value.lower())


def _is_under(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _category_paths(assets_root: Path) -> list[Path]:
    root = (
        assets_root
        / "Bellwright"
        / "Content"
        / "Mist"
        / "Data"
        / "Items"
        / "Categories"
    )

    if not root.exists():
        return []

    return sorted(
        (
            path
            for path in discover_json(assets_root)
            if _is_under(path, root)
            and any(
                _superstruct_name(obj) in CATEGORY_CLASSES
                for obj in _load_objects(path)
            )
        ),
        key=lambda path: str(path).lower(),
    )


class CategoryIndex:
    def __init__(
        self,
        index: dict[str, str],
        titles: dict[str, str],
        children: dict[str, set[str]],
    ):
        self.index = index
        self.titles = titles
        self.children = children

    @classmethod
    def from_paths(cls, paths: list[Path]) -> "CategoryIndex":
        index: dict[str, str] = {}
        titles: dict[str, str] = {}
        parents: dict[str, str | None] = {}

        for path in paths:
            objects = _load_objects(path)

            name = next(
                (n for obj in objects if (n := _property_name(obj))),
                None,
            )

            if not name:
                continue

            key = normalize_category_key(name)

            titles[key] = name
            index[key] = name
            index[normalize_category_key(path.stem)] = name

            for obj in objects:
                object_name = obj.get("Name")

                if isinstance(object_name, str):
                    index[normalize_category_key(object_name)] = name

                properties = obj.get("Properties")

                if isinstance(properties, dict):
                    parent = category_key_from_ref(properties.get("Parent"))
                    parents[key] = normalize_category_key(parent) if parent else None

        children = {key: set() for key in titles}

        for key, parent in parents.items():
            if parent in titles:
                children[parent].add(key)

        return cls(index, titles, children)

    def get_category(self, value: Any) -> str | None:
        key = category_key_from_ref(value)

        if not key:
            return None

        normalized = normalize_category_key(key)

        if normalized in self.index:
            return self.index[normalized]

        return next(
            (
                title
                for candidate, title in sorted(
                    self.index.items(),
                    key=lambda item: -len(item[0]),
                )
                if normalized.startswith(candidate)
            ),
            None,
        )

    def scope(self, title: str) -> set[str]:
        start = normalize_category_key(title)
        scope: set[str] = set()
        stack = [start]

        while stack:
            current = stack.pop()

            if current in scope:
                continue

            scope.add(current)
            stack.extend(self.children.get(current, ()))

        return scope

    def child_titles(self, title: str) -> list[str]:
        key = normalize_category_key(title)

        return sorted(
            (self.titles[k] for k in self.children.get(key, ())),
            key=str.lower,
        )

    @staticmethod
    def slug(title: str) -> str:
        return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or "category"


def build_category_index(assets_root: Path) -> CategoryIndex:
    return CategoryIndex.from_paths(_category_paths(assets_root))


def category_slug(value: str) -> str:
    return CategoryIndex.slug(value)


def category_name_for(
    properties: dict,
    category_index: CategoryIndex,
) -> str | None:
    return category_index.get_category(properties.get("Category"))


def build_category_hierarchy(
    assets_root: Path,
) -> tuple[dict[str, set[str]], dict[str, str]]:
    index = build_category_index(assets_root)
    return index.children, index.titles


def category_row_scope(
    title: str,
    descendants: dict[str, set[str]],
) -> set[str]:
    start = normalize_category_key(title)
    scope: set[str] = set()
    stack = [start]

    while stack:
        current = stack.pop()

        if current in scope:
            continue

        scope.add(current)
        stack.extend(descendants.get(current, ()))

    return scope


def is_equipment_item_path(path: Path) -> bool:
    parts = {part.lower() for part in path.parts}
    return {"items", "equipment"} <= parts and "categories" not in parts


def is_equipment_category_path(path: Path) -> bool:
    parts = {part.lower() for part in path.parts}
    return {"items", "categories", "equipment"} <= parts


def is_equipment_category_group(path: Path) -> bool:
    return False


__all__ = [
    "CategoryIndex",
    "build_category_index",
    "build_category_hierarchy",
    "category_key_from_ref",
    "category_name_for",
    "category_row_scope",
    "category_slug",
    "normalize_category_key",
    "is_equipment_item_path",
    "is_equipment_category_path",
    "is_equipment_category_group",
]
