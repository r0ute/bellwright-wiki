from __future__ import annotations

import json
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from ..discover import discover_json
from .category import CategoryIndex
from .classifier import source_family
from .model import Item


def load_objects(path: Path) -> list[dict[str, Any]]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if isinstance(raw, list):
        return [x for x in raw if isinstance(x, dict)]
    return [raw] if isinstance(raw, dict) else []


def find_cdo(objects: list[dict[str, Any]]) -> dict[str, Any] | None:
    return next((o for o in objects if isinstance(o.get("Properties"), dict)), None)


def load_cdo(path: Path) -> dict[str, Any]:
    return find_cdo(load_objects(path)) or {}


def load_properties(path: Path) -> dict[str, Any]:
    p = load_cdo(path).get("Properties")
    return p if isinstance(p, dict) else {}


def string_value(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        for k in (
            "LocalizedString",
            "SourceString",
            "Value",
            "ObjectName",
            "AssetPathName",
            "ObjectPath",
        ):
            v = value.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()
    return ""


def game_path(value: Any) -> str:
    if not isinstance(value, dict):
        return ""
    for k in ("ObjectPath", "AssetPathName", "ObjectName"):
        v = value.get(k)
        if not isinstance(v, str) or not v:
            continue
        m = re.search(r"(/Game/[^']+)", v)
        if m:
            return m.group(1)
        m = re.search(r"'([^']+)'", v)
        if m:
            return m.group(1)
        if v.startswith("/Game/"):
            return v
    return ""


def path_from_game_object(assets_root: Path, object_path: str) -> Path | None:
    if not object_path.startswith("/Game/"):
        return None
    rel = object_path.removeprefix("/Game/").split(".", 1)[0]
    p = assets_root / "Bellwright" / "Content" / (rel + ".json")
    return p if p.exists() else None


def template_category(
    path: Path, props: dict[str, Any], index: CategoryIndex, assets_root: Path
):
    node = index.category_for_ref(props.get("Category"))
    if node:
        return node
    current = path
    seen = set()
    while current not in seen:
        seen.add(current)
        cdo = load_cdo(current)
        cp = cdo.get("Properties")
        if not isinstance(cp, dict):
            return None
        node = index.category_for_ref(cp.get("Category"))
        if node:
            return node
        nxt = path_from_game_object(assets_root, game_path(cdo.get("Template")))
        if not nxt:
            return None
        current = nxt
    return None


def template_name(cdo: dict[str, Any]) -> str:
    value = cdo.get("Template")
    if isinstance(value, dict):
        value = (
            value.get("ObjectName")
            or value.get("ObjectPath")
            or value.get("AssetPathName")
        )
    if not isinstance(value, str):
        return ""
    m = re.search(r"'([^']+)'", value)
    value = m.group(1) if m else value
    return (
        value.rsplit("/", 1)[-1]
        .split(".", 1)[0]
        .removeprefix("Default__")
        .removesuffix("_C")
    )


def discover_items(assets_root: Path, index: CategoryIndex) -> Iterator[Item]:
    categories_root = (
        assets_root
        / "Bellwright"
        / "Content"
        / "Mist"
        / "Data"
        / "Items"
        / "Categories"
    )
    for path in discover_json(assets_root):
        try:
            path.relative_to(categories_root)
            continue
        except ValueError:
            pass
        cdo = load_cdo(path)
        props = cdo.get("Properties")
        if not isinstance(props, dict):
            continue
        name = string_value(props.get("Name"))
        if not name:
            continue
        node = template_category(path, props, index, assets_root)
        if node is None or node.is_group:
            continue
        group = index.group_for(node)
        yield Item(
            path=path,
            source_family=source_family(path),
            template=template_name(cdo),
            category_key=node.key,
            category=node.title,
            category_group_key=group.key if group else None,
            category_group=group.title if group else None,
            name=name,
            properties=props,
        )


def reference_name(value: Any) -> str:
    ref = game_path(value)
    if ref:
        return ref.rsplit("/", 1)[-1].split(".", 1)[0].removesuffix("_C")
    return ""


def load_broken_relationships(assets_root: Path) -> dict[str, tuple[str, str]]:
    result = {}
    for path in discover_json(assets_root):
        if source_family(path).lower() != "brokenitems":
            continue
        props = load_properties(path)
        damaged = reference_name(props.get("DamagedItem"))
        parent = reference_name(props.get("UnbrokenParentItem"))
        if damaged or parent:
            result[path.stem] = (damaged, parent)
    return result
