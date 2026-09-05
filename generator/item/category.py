from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..discover import discover_json

CATEGORY_CLASSES = frozenset({"MistItemCategory", "MistItemCategory_C"})
CATEGORY_GROUP_CLASSES = frozenset({"MistItemCategoryGroup", "MistItemCategoryGroup_C"})


def _objects(path: Path) -> list[dict[str, Any]]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if isinstance(raw, list):
        return [x for x in raw if isinstance(x, dict)]
    return [raw] if isinstance(raw, dict) else []


def _reference(value: Any) -> str | None:
    if not isinstance(value, dict):
        return None
    for key in ("ObjectPath", "AssetPathName", "ObjectName"):
        raw = value.get(key)
        if not isinstance(raw, str) or not raw:
            continue
        if raw.startswith("/Game/"):
            return raw.split(".", 1)[0]
        match = re.search(r"'([^']+)'", raw)
        if match:
            return match.group(1)
    return None


def object_path_key(value: Any) -> str | None:
    ref = _reference(value)
    if not ref:
        return None
    return ref.rsplit("/", 1)[-1].removesuffix("_C")


def normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower().removesuffix("_c"))


def _superstruct(obj: dict[str, Any]) -> str:
    return object_path_key(obj.get("SuperStruct")) or ""


def _name(obj: dict[str, Any]) -> str | None:
    props = obj.get("Properties")
    if not isinstance(props, dict):
        return None
    value = props.get("Name")
    if isinstance(value, dict):
        value = value.get("LocalizedString") or value.get("SourceString")
    return value.strip() if isinstance(value, str) and value.strip() else None


def _is_category_file(path: Path, categories_root: Path) -> bool:
    try:
        path.relative_to(categories_root)
    except ValueError:
        return False
    return True


@dataclass(slots=True)
class CategoryNode:
    key: str
    class_name: str
    title: str
    path: Path
    parent_key: str | None
    is_group: bool
    children: list[str] = field(default_factory=list)


class CategoryIndex:
    def __init__(self, nodes: dict[str, CategoryNode]):
        self.nodes = nodes
        self.by_class: dict[str, list[str]] = {}
        for key, node in nodes.items():
            self.by_class.setdefault(normalize_key(node.class_name), []).append(key)

    @classmethod
    def from_assets(cls, assets_root: Path) -> "CategoryIndex":
        root = (
            assets_root
            / "Bellwright"
            / "Content"
            / "Mist"
            / "Data"
            / "Items"
            / "Categories"
        )
        nodes: dict[str, CategoryNode] = {}
        pending: list[tuple[Path, str, str, str | None, bool]] = []
        for path in discover_json(assets_root):
            if not _is_category_file(path, root):
                continue
            objects = _objects(path)
            class_obj = next(
                (
                    o
                    for o in objects
                    if _superstruct(o) in CATEGORY_CLASSES | CATEGORY_GROUP_CLASSES
                ),
                None,
            )
            if not class_obj:
                continue
            class_name = str(class_obj.get("Name") or path.stem)
            class_name = class_name.removesuffix("_C")
            is_group = _superstruct(class_obj) in CATEGORY_GROUP_CLASSES
            cdo = next(
                (o for o in objects if isinstance(o.get("Properties"), dict)), None
            )
            title = _name(cdo or {}) or path.stem
            parent = (
                object_path_key((cdo or {}).get("Properties", {}).get("Parent"))
                if cdo
                else None
            )
            key = str(path.relative_to(root)).replace("\\", "/").rsplit(".", 1)[0]
            pending.append((path, key, class_name, parent, is_group))
        # First pass: resolve exact asset identities from package paths.
        path_to_key = {
            str(p.relative_to(root)).replace("\\", "/").rsplit(".", 1)[0]: k
            for p, k, _, _, _ in pending
        }
        class_to_keys: dict[str, list[str]] = {}
        for path, key, class_name, parent, is_group in pending:
            cdo = next(
                (o for o in _objects(path) if isinstance(o.get("Properties"), dict)), {}
            )
            pref = _reference(cdo.get("Properties", {}).get("Parent"))
            parent_key = None
            if pref and pref.startswith("/Game/"):
                rel = pref.removeprefix("/Game/").split(".", 1)[0]
                marker = "Mist/Data/Items/Categories/"
                if rel.startswith(marker):
                    parent_key = path_to_key.get(rel[len(marker) :])
            node = CategoryNode(
                key, class_name, _name(cdo) or path.stem, path, parent_key, is_group
            )
            nodes[key] = node
            class_to_keys.setdefault(normalize_key(class_name), []).append(key)
        for node in nodes.values():
            if node.parent_key in nodes:
                nodes[node.parent_key].children.append(node.key)
        return cls(nodes)

    def resolve_ref(self, value: Any) -> CategoryNode | None:
        ref = _reference(value)
        if not ref:
            return None
        marker = "/Game/Mist/Data/Items/Categories/"
        if ref.startswith(marker):
            rel = ref[len(marker) :]
            key = rel.rsplit("/", 1)[-1]
            node = self.nodes.get(rel)
            if node:
                return node
            node = self.nodes.get(rel.rsplit(".", 1)[0])
            if node:
                return node
        key = object_path_key(value)
        if key:
            matches = self.by_class.get(normalize_key(key), [])
            if len(matches) == 1:
                return self.nodes[matches[0]]
        return None

    def category_for_ref(self, value: Any) -> CategoryNode | None:
        node = self.resolve_ref(value)
        if node and not node.is_group:
            return node
        return node

    def group_for(self, node: CategoryNode | None) -> CategoryNode | None:
        seen = set()
        while node and node.key not in seen:
            seen.add(node.key)
            if node.is_group:
                return node
            node = self.nodes.get(node.parent_key) if node.parent_key else None
        return None

    def children(self, node: CategoryNode, categories_only=True) -> list[CategoryNode]:
        result = []
        for key in sorted(node.children, key=lambda k: self.nodes[k].title.lower()):
            child = self.nodes[key]
            if not categories_only or not child.is_group:
                result.append(child)
        return result

    def roots(self) -> list[CategoryNode]:
        return sorted(
            (n for n in self.nodes.values() if n.parent_key is None),
            key=lambda n: n.title.lower(),
        )

    @staticmethod
    def slug(title: str) -> str:
        return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or "category"


def build_category_index(assets_root: Path) -> CategoryIndex:
    return CategoryIndex.from_assets(assets_root)


def category_slug(value: str) -> str:
    return CategoryIndex.slug(value)


def normalize_category_key(value: str) -> str:
    return normalize_key(value)
