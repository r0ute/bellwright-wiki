from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from .. import icon
from . import category, markdown, scanner
from .model import Item
from .schema.common import FieldExtractor
from .schema.mapping import schema_module

TITLE = "Items"


def _fields_for(item: Item, index: category.CategoryIndex) -> dict[str, FieldExtractor]:
    node = index.nodes[item.category_key]
    module = schema_module(index, node, item.template)
    return dict(getattr(module, "FIELDS", {}))


def _item_context(item: Item, icon_index, icon_out: Path, icon_prefix: str):
    context = {
        "path": item.path,
        "source_family": item.source_family,
        "template": item.template,
        "category": item.category,
        "category_group": item.category_group or "",
        "icon": "",
        "damaged_item": item.damaged_item,
        "unbroken_parent": item.unbroken_parent,
    }
    icon_path = icon.find_icon(item.properties, icon_index)
    if icon_path:
        destination = icon.copy_icon(icon_path, icon_out)
        context["icon"] = (
            f'<img src="{icon_prefix}assets/icons/{destination.name}" '
            f'alt="{item.stem}" width="48">'
        )
    return context


def _rows(items, index, icon_index, icon_out, icon_prefix):
    if not items:
        return [], []
    field_sets = [_fields_for(item, index) for item in items]
    headers: list[str] = []
    for fields in field_sets:
        for name in fields:
            if name not in headers:
                headers.append(name)
    rows = []
    for item, fields in zip(items, field_sets):
        context = _item_context(item, icon_index, icon_out, icon_prefix)
        rows.append(
            {
                name: extractor(item.properties, context)
                for name, extractor in fields.items()
            }
        )
    rows.sort(key=lambda row: str(row.get("Name", "")).lower())
    return headers, rows


def _relationship_maps(assets):
    by_parent: dict[str, str] = {}
    by_broken: dict[str, str] = {}
    for broken, (damaged, parent) in scanner.load_broken_relationships(assets).items():
        damaged = damaged or broken
        if parent:
            by_parent[parent] = damaged
        by_broken[damaged] = parent
    return by_parent, by_broken


def _apply_relationships(items, assets):
    by_parent, by_broken = _relationship_maps(assets)
    for item in items:
        item.damaged_item = by_parent.get(item.stem, "")
        item.unbroken_parent = by_broken.get(item.stem, "")


def _group_ancestors(
    index: category.CategoryIndex, node: category.CategoryNode
) -> list[category.CategoryNode]:
    ancestors = []
    current = index.nodes.get(node.parent_key) if node.parent_key else None
    while current:
        if current.is_group:
            ancestors.append(current)
        current = index.nodes.get(current.parent_key) if current.parent_key else None
    ancestors.reverse()
    return ancestors


def _page_path(index: category.CategoryIndex, node: category.CategoryNode) -> str:
    parts = [
        category.CategoryIndex.slug(group.title)
        for group in _group_ancestors(index, node)
    ]
    if node.is_group:
        parts.append(category.CategoryIndex.slug(node.title))
        parts.append("index.md")
    else:
        parts.append(category.CategoryIndex.slug(node.title) + ".md")
    return "/".join(["items", *parts])


def _page_parent(index: category.CategoryIndex, node: category.CategoryNode):
    ancestors = _group_ancestors(index, node)
    if not ancestors:
        return None, None
    parent = ancestors[-1]
    grand = ancestors[-2] if len(ancestors) > 1 else None
    return parent, grand


def generate(
    assets: Path, docs: Path, icon_out: Path, icon_index: dict[str, Path]
) -> dict:
    index = category.build_category_index(assets)
    items = list(scanner.discover_items(assets, index))
    _apply_relationships(items, assets)
    by_category = defaultdict(list)
    for item in items:
        by_category[item.category_key].append(item)

    item_root = docs / "items"
    generated: list[str] = []

    # Every category gets its own page. Categories with no current rows still
    # receive a page so the asset-defined taxonomy remains stable.
    for node in sorted(
        (n for n in index.nodes.values() if not n.is_group),
        key=lambda n: n.title.lower(),
    ):
        ancestors = _group_ancestors(index, node)
        output = item_root.joinpath(
            *(category.CategoryIndex.slug(g.title) for g in ancestors),
            category.CategoryIndex.slug(node.title) + ".md",
        )
        relative_depth = len(ancestors) + 1
        icon_prefix = "../" * relative_depth
        headers, rows = _rows(
            by_category.get(node.key, []), index, icon_index, icon_out, icon_prefix
        )
        parent, grand = _page_parent(index, node)
        markdown.write_page(
            output,
            node.title,
            rows=rows,
            headers=headers,
            parent=parent.title if parent else None,
            parent_path=_page_path(index, parent) if parent else None,
            grand_parent=grand.title if grand else None,
            grand_parent_path=_page_path(index, grand) if grand else None,
        )
        generated.append(str(output.relative_to(docs)).replace("\\", "/"))

    # Every group gets its own page. The page contains direct categories and
    # nested groups, but never item rows.
    for group in sorted(
        (n for n in index.nodes.values() if n.is_group), key=lambda n: n.title.lower()
    ):
        ancestors = _group_ancestors(index, group)
        output = item_root.joinpath(
            *(category.CategoryIndex.slug(g.title) for g in ancestors),
            category.CategoryIndex.slug(group.title),
            "index.md",
        )
        links = []
        stack = list(index.children(group, categories_only=False))
        descendants = []
        while stack:
            child = stack.pop()
            if child.is_group:
                stack.extend(index.children(child, categories_only=False))
            else:
                descendants.append(child)
        for child in sorted(descendants, key=lambda n: n.title.lower()):
            links.append(
                (child.title, _relative_link(output, docs / _page_path(index, child)))
            )
        parent, grand = _page_parent(index, group)
        markdown.write_page(
            output,
            group.title,
            links=links,
            parent=parent.title if parent else None,
            parent_path=_page_path(index, parent) if parent else None,
            grand_parent=grand.title if grand else None,
            grand_parent_path=_page_path(index, grand) if grand else None,
        )
        generated.append(str(output.relative_to(docs)).replace("\\", "/"))

    # The root page contains only root groups and root categories.
    root_links = []
    for node in index.roots():
        root_links.append(
            (
                node.title,
                _relative_link(item_root / "items.md", docs / _page_path(index, node)),
            )
        )
    markdown.write_page(item_root / "items.md", TITLE, links=root_links)
    generated.append("items/items.md")

    print(f"Item definitions discovered: {len(items)}")
    return {"title": TITLE, "pages": [{"title": p, "slug": p[:-3]} for p in generated]}


def _relative_link(source: Path, target: Path) -> str:
    return Path(__import__("os").path.relpath(target, source.parent)).as_posix()
