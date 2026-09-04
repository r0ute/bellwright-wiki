"""Compatibility layer for the generalized item category index."""

from ..item.category import (
    CategoryIndex,
    build_category_index,
    category_key_from_ref,
    normalize_category_key,
)


def category_name_for(properties: dict, category_index: CategoryIndex) -> str | None:
    return category_index.get_category(properties.get("Category"))


def build_category_hierarchy(assets_root):
    index = build_category_index(assets_root)
    return index.children, index.titles


def category_row_scope(title, descendants):
    start = normalize_category_key(title)
    scope = set()
    stack = [start]
    while stack:
        current = stack.pop()
        if current in scope:
            continue
        scope.add(current)
        stack.extend(descendants.get(current, ()))
    return scope


def is_equipment_item_path(path):
    parts = {part.lower() for part in path.parts}
    return {"items", "equipment"} <= parts and "categories" not in parts


def is_equipment_category_path(path):
    parts = {part.lower() for part in path.parts}
    return {"items", "categories", "equipment"} <= parts


def is_equipment_category_group(path):
    return False


category_slug = CategoryIndex.slug

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
