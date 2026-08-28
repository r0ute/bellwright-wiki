from pathlib import Path
import json
import re

from categories import (
    category_name_for_path,
    is_equipment_category_path,
    is_equipment_category_group,
    is_equipment_item_path,
)
from discover import discover_json
from icons import build_icon_index, copy_icon, find_icon
from markdown import write_generation_report, write_page


ROOT = Path(__file__).resolve().parent.parent

ASSETS = ROOT / "assets"
DOCS = ROOT / "docs"
ICON_OUT = DOCS / "assets" / "icons"


def find_cdo(objects: list) -> dict | None:
    return next(
        (
            obj
            for obj in objects
            if isinstance(obj, dict)
            and isinstance(obj.get("Properties"), dict)
        ),
        None,
    )


def asset_name(path: Path, objects: list) -> str:
    cdo = find_cdo(objects)

    if not cdo:
        return path.stem

    name = cdo["Properties"].get("Name")

    if isinstance(name, dict):
        return (
            name.get("LocalizedString")
            or name.get("SourceString")
            or path.stem
        )

    if isinstance(name, str) and name:
        return name

    return path.stem


def normalize_category_key(value: str) -> str:
    cleaned = value.strip()

    if cleaned.endswith("_C"):
        cleaned = cleaned[:-2]

    return re.sub(r"[^a-z0-9]", "", cleaned.lower())


def category_key_from_ref(value: object) -> str | None:
    if not isinstance(value, dict):
        return None

    for key in ("ObjectPath", "AssetPathName", "ObjectName"):
        ref = value.get(key)

        if not isinstance(ref, str) or not ref:
            continue

        if ref.startswith("/Game/"):
            return ref.split("/")[-1].split(".")[0]

        match = re.search(r"'([^']+)'", ref)
        if match:
            return match.group(1)

    return None


def build_category_index(assets_root: Path) -> dict[str, str]:
    category_index: dict[str, str] = {}

    for path in discover_json(assets_root):
        if not is_equipment_category_path(path):
            continue

        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue

        objects = raw if isinstance(raw, list) else [raw]
        cdo = find_cdo(objects)

        if not cdo:
            continue

        name = asset_name(path, objects)
        category_index[normalize_category_key(name)] = name
        category_index[normalize_category_key(path.stem)] = name
        category_index[normalize_category_key(f"{path.stem}_C")] = name

    return category_index


def category_name_for(properties: dict, category_index: dict[str, str]) -> str | None:
    category_ref = properties.get("Category")
    key = category_key_from_ref(category_ref)

    if not key:
        return None

    normalized = normalize_category_key(key)
    # Direct match first
    title = category_index.get(normalized)
    if title:
        return title

    # Fallback: if an exact category file for the referenced key doesn't
    # exist, try matching it to a parent/group category by prefix. For
    # example, Ammo_Arrows -> matches the Ammo group that was indexed.
    for candidate_key, candidate_title in sorted(category_index.items(), key=lambda it: -len(it[0])):
        if normalized.startswith(candidate_key):
            return candidate_title

    return None


def generate_equipment_item(
    path: Path,
    objects: list,
    icon_index: dict[str, Path],
    category_index: dict[str, str],
) -> dict:
    cdo = find_cdo(objects)

    if not cdo:
        raise ValueError(f"No CDO found: {path}")

    properties = cdo.get("Properties", {})

    name = asset_name(path, objects)
    category_name = category_name_for(properties, category_index) or "Uncategorized"

    icon = find_icon(properties, icon_index)

    icon_md = "—"

    if icon:
        destination = copy_icon(icon, ICON_OUT)

        icon_md = (
            f'<img src="assets/icons/{destination.name}" '
            f'alt="{name}" width="48">'
        )

    context = {
        "name": name,
        "icon": icon_md,
        "path": path,
    }

    # Return minimal representation (properties + context); rendering will
    # use schema-specific extractors to create final table rows.
    return {
        "properties": properties,
        "context": context,
        "Category": category_name,
    }


def category_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "category"


def equipment_category_paths(assets_root: Path) -> list[Path]:
    category_root = assets_root / "Bellwright" / "Content" / "Mist" / "Data" / "Items" / "Categories" / "Equipment"
    if not category_root.exists():
        return []

    seen: set[str] = set()
    paths: list[Path] = []

    for path in sorted(discover_json(assets_root), key=lambda item: str(item).lower()):
        if not path.is_relative_to(category_root):
            continue

        title = category_name_for_path(path)
        if not title:
            continue

        key = normalize_category_key(title)
        if key in seen:
            continue

        seen.add(key)
        paths.append(path)

    return paths


def build_category_hierarchy(assets_root: Path) -> tuple[dict[str, set[str]], dict[str, str]]:
    titles: dict[str, str] = {}
    paths: list[Path] = []

    for path in discover_json(assets_root):
        if not is_equipment_category_path(path):
            continue

        title = category_name_for_path(path)
        if not title:
            continue

        key = normalize_category_key(title)
        titles[key] = title
        paths.append(path)

    children: dict[str, set[str]] = {key: set() for key in titles}

    for path in paths:
        title = category_name_for_path(path)
        if not title:
            continue

        key = normalize_category_key(title)

        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue

        objects = raw if isinstance(raw, list) else [raw]
        for obj in objects:
            if not isinstance(obj, dict):
                continue
            props = obj.get("Properties")
            if not isinstance(props, dict):
                continue
            parent = props.get("Parent")
            if not isinstance(parent, dict):
                continue

            parent_key = category_key_from_ref(parent)
            if not parent_key:
                continue

            parent_key = normalize_category_key(parent_key)
            if not parent_key:
                continue

            if parent_key not in titles:
                parent_key = "equipment"

            children.setdefault(parent_key, set()).add(key)

    if "equipment" not in children:
        children["equipment"] = set(titles)

    return children, titles


def category_row_scope(title: str, descendants: dict[str, set[str]], titles: dict[str, str]) -> set[str]:
    start = normalize_category_key(title)
    scope: set[str] = set()
    stack = [start]

    while stack:
        current = stack.pop()
        if current in scope:
            continue
        scope.add(current)
        stack.extend(sorted(descendants.get(current, set()), key=str.lower, reverse=True))

    return scope


def write_index_page(output: Path, categories: list[dict]) -> None:
    lines = [
        "---",
        "layout: default",
        "title: Bellwright Data",
        "---",
        "",
        "# Bellwright Data",
        "",
        "## Categories",
        "",
    ]

    for category in sorted(categories, key=lambda item: item["title"].lower()):
        lines.append(
            f'- [{category["title"]}]({category["slug"]})'
        )

    lines.extend([
        "",
        "## Reports",
        "",
        "- [Generation report](generation-report)",
        "",
    ])

    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    for stale in DOCS.glob("*.md"):
        stale.unlink()

    print(f"Assets: {ASSETS}")
    print(f"Docs:   {DOCS}")

    icon_index = build_icon_index(ASSETS)
    category_index = build_category_index(ASSETS)

    print(f"Icons indexed: {len(icon_index)}")
    print(f"Categories indexed: {len(category_index)}")

    equipment_items = []
    equipment_raw: list[tuple[Path, dict]] = []
    scanned = 0
    category_pages: list[dict] = []
    seen_category_slugs: set[str] = set()

    for path in discover_json(ASSETS):
        scanned += 1

        if not is_equipment_item_path(path):
            continue

        try:
            raw = json.loads(
                path.read_text(encoding="utf-8")
            )
        except Exception as exc:
            print(f"SKIP {path}: {exc}")
            continue

        if not isinstance(raw, list):
            raw = [raw]

        cdo = find_cdo(raw)
        if not cdo:
            continue

        # store raw properties for schema inference
        props = cdo.get("Properties", {})
        equipment_raw.append((path, props))

        equipment_items.append(
            generate_equipment_item(
                path,
                raw,
                icon_index,
                category_index,
            )
        )

    # default headers fallback (used if no schema module found)
    default_headers = ["Icon", "Name", "Category", "Price"]
    category_children, category_titles = build_category_hierarchy(ASSETS)

    # Generate per-group schema files under generator/schemas by sampling a few
    # items from each group. This writes new schema modules only when they do
    # not already exist. A default fallback schema is created as well.
    def pretty_label(key: str) -> str:
        # Convert camel/Pascal/underscore keys to Title Case labels
        import re

        s = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", key)
        s = s.replace("_", " ")
        return s.strip().title()

    def make_schema_module(slug: str, labels: list[str], keys: list[str]) -> str:
        # Create a simple schema module text that defines EQUIPMENT_FIELDS
        # using the common helpers.
        lines = [
            "from __future__ import annotations",
            "from typing import Any",
            "try:",
            "    from generator.schemas.common import (",
            "        FieldExtractor,",
            "        extract_value,",
            "        field,",
            "    )",
            "except ModuleNotFoundError:",
            "    from schemas.common import (",
            "        FieldExtractor,",
            "        extract_value,",
            "        field,",
            "    )",
            "",
            "EQUIPMENT_FIELDS: dict[str, FieldExtractor] = {",
            "    \"Icon\": lambda _p, ctx: ctx['icon'],",
            "    \"Name\": lambda _p, ctx: ctx['name'],",
        ]

        for label, key in zip(labels, keys):
            # don't re-add Name/Icon
            if label in ("Icon", "Name"):
                continue
            # use field extractor for the raw key
            lines.append(f"    \"{label}\": field(\"{key}\"),")

        lines.append("}")
        return "\n".join(lines)

    import os
    schemas_dir = Path(__file__).resolve().parent / "schemas"
    schemas_dir.mkdir(parents=True, exist_ok=True)

    # ensure default fallback schema exists
    default_path = schemas_dir / "default.py"
    if not default_path.exists():
        default_content = (
            "from __future__ import annotations\n"
            "from typing import Any\n"
            "try:\n"
            "    from generator.schemas.common import (\n"
            "        FieldExtractor,\n"
            "        extract_value,\n"
            "        field,\n"
            "    )\n"
            "except ModuleNotFoundError:\n"
            "    from schemas.common import (\n"
            "        FieldExtractor,\n"
            "        extract_value,\n"
            "        field,\n"
            "    )\n\n"
            "EQUIPMENT_FIELDS: dict[str, FieldExtractor] = {\n"
            "    \"Icon\": lambda _p, ctx: ctx['icon'],\n"
            "    \"Name\": lambda _p, ctx: ctx['name'],\n"
            "    \"Category\": field('Category'),\n"
            "    \"Price\": field('ExpectedPrice'),\n"
            "}\n"
        )
        default_path.write_text(default_content, encoding="utf-8")

    # For each group, sample up to 3 item property dicts and create a schema
    for path in equipment_category_paths(ASSETS):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue

        if not is_equipment_category_group(path):
            continue

        title = category_name_for_path(path)
        if not title:
            continue
        key = normalize_category_key(title)
        slug = category_slug(path.stem)

        # collect up to 3 samples that belong to this group's scope
        scope = category_row_scope(title, category_children, category_titles)
        samples: list[dict] = []
        for i_path, props in equipment_raw:
            # find this item's category key
            cat_name = category_name_for(props, category_index)
            if not cat_name:
                continue
            if normalize_category_key(cat_name) in scope:
                samples.append(props)
            if len(samples) >= 3:
                break

        if not samples:
            continue

        # determine common property keys among samples (union)
        union_keys: list[str] = []
        seen_keys: set[str] = set()
        for props in samples:
            for k in props.keys():
                if k in ("Name", "Icon", "Category"):
                    continue
                if k not in seen_keys:
                    seen_keys.add(k)
                    union_keys.append(k)
        # limit to first 8 keys
        chosen_keys = union_keys[:8]
        labels = [pretty_label(k) for k in chosen_keys]

        target_file = schemas_dir / f"{slug}.py"
        if target_file.exists():
            # do not overwrite existing schema files
            continue

        content = make_schema_module(slug, labels, chosen_keys)
        target_file.write_text(content, encoding="utf-8")

    processed_keys: set[str] = set()

    # Collect category paths once and build a quick lookup
    category_paths = list(equipment_category_paths(ASSETS))

    # Map normalized title -> path (useful if needed)
    path_by_key: dict[str, Path] = {}
    for path in category_paths:
        title = category_name_for_path(path)
        if not title:
            continue
        path_by_key[normalize_category_key(title)] = path

    # Phase 1: emit pages for category groups (standalone .md with sections)
    for path in sorted(category_paths, key=lambda p: str(p).lower()):
        if not is_equipment_category_group(path):
            continue

        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue

        objects = raw if isinstance(raw, list) else [raw]
        cdo = find_cdo(objects)
        if not cdo:
            continue

        title = asset_name(path, objects)
        key = normalize_category_key(title)
        if key in processed_keys:
            continue

        slug = category_slug(path.stem)

        # Build sections: if the group has child categories, emit only
        # the child-category tables. If the group has no children, emit a
        # single table for the group (full scope). Sections map to
        # (headers, rows) pairs so each child can have its own schema.
        sections: dict[str, tuple[list[str], list[dict]]] = {}

        child_keys = sorted(category_children.get(key, set()), key=lambda k: category_titles.get(k, ""))

        import importlib

        if child_keys:
            # Emit only child sections; do not include a group's own table.
            for child_key in child_keys:
                child_title = category_titles.get(child_key)
                if not child_title:
                    continue

                child_path = path_by_key.get(child_key)
                # If the child is itself a category group file, skip it here
                # so that it will be emitted as its own standalone page later.
                if child_path and is_equipment_category_group(child_path):
                    continue

                child_scope = category_row_scope(child_title, category_children, category_titles)
                child_items = [
                    item for item in equipment_items
                    if normalize_category_key(item["Category"]) in child_scope
                ]

                # Select schema for this child: prefer generator.schemas.<slug>, else default
                schema_mod = None
                if child_path:
                    child_slug = category_slug(child_path.stem)
                    try:
                        schema_mod = importlib.import_module(f"generator.schemas.{child_slug}")
                    except Exception:
                        schema_mod = None

                if schema_mod is None:
                    try:
                        schema_mod = importlib.import_module("generator.schemas.default")
                    except Exception:
                        schema_mod = None

                if schema_mod is not None:
                    schema_fields = list(schema_mod.EQUIPMENT_FIELDS.keys())
                    rendered_rows: list[dict] = []
                    for item in child_items:
                        props = item["properties"]
                        ctx = item["context"]
                        row = {}
                        for field_name, extractor in schema_mod.EQUIPMENT_FIELDS.items():
                            try:
                                row[field_name] = extractor(props, ctx)
                            except Exception:
                                row[field_name] = "—"
                        rendered_rows.append(row)
                else:
                    # fallback minimal
                    schema_fields = default_headers
                    rendered_rows = [
                        {
                            "Icon": item["context"]["icon"],
                            "Name": item["context"]["name"],
                            "Category": item.get("Category"),
                            "Price": item["properties"].get("ExpectedPrice") or item["properties"].get("Price") or "—",
                        }
                        for item in child_items
                    ]

                rendered_rows = sorted(rendered_rows, key=lambda r: str(r.get("Name", "")).lower())
                sections[child_title] = (schema_fields, rendered_rows)
                processed_keys.add(child_key)

            # Mark the group as processed so it won't be emitted separately.
            processed_keys.add(key)
        else:
            # No child categories: emit a full-scope table for the group.
            group_scope = category_row_scope(title, category_children, category_titles)
            group_items = [
                item for item in equipment_items
                if normalize_category_key(item["Category"]) in group_scope
            ]

            # select schema for this group
            schema_mod = None
            try:
                schema_mod = importlib.import_module(f"generator.schemas.{slug}")
            except Exception:
                try:
                    schema_mod = importlib.import_module("generator.schemas.default")
                except Exception:
                    schema_mod = None

            if schema_mod is not None:
                schema_fields = list(schema_mod.EQUIPMENT_FIELDS.keys())
            else:
                schema_fields = default_headers

            rendered_rows = []
            for item in group_items:
                props = item["properties"]
                ctx = item["context"]
                row = {}
                if schema_mod is not None:
                    for field_name, extractor in schema_mod.EQUIPMENT_FIELDS.items():
                        try:
                            row[field_name] = extractor(props, ctx)
                        except Exception:
                            row[field_name] = "—"
                else:
                    row["Icon"] = ctx["icon"]
                    row["Name"] = ctx["name"]
                    row["Category"] = item.get("Category")
                    row["Price"] = props.get("ExpectedPrice") or props.get("Price") or "—"

                rendered_rows.append(row)

            rendered_rows = sorted(rendered_rows, key=lambda r: str(r.get("Name", "")).lower())
            sections[title] = (schema_fields, rendered_rows)
            processed_keys.add(key)

        total = sum(len(r) for _, r in sections.values())
        if slug not in seen_category_slugs:
            category_pages.append({"title": title, "slug": slug})
            seen_category_slugs.add(slug)

        write_page(
            DOCS / f"{slug}.md",
            title=title,
            description=(
                f"{total} matching assets in the {title} category."
            ),
            headers=default_headers,
            sections=sections,
        )

    # Phase 2: emit pages for remaining non-group categories
    for path in sorted(category_paths, key=lambda p: str(p).lower()):
        if is_equipment_category_group(path):
            continue

        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue

        objects = raw if isinstance(raw, list) else [raw]
        cdo = find_cdo(objects)
        if not cdo:
            continue

        title = asset_name(path, objects)
        key = normalize_category_key(title)
        if key in processed_keys:
            continue

        slug = category_slug(path.stem)
        scope = category_row_scope(title, category_children, category_titles)
        items = [
            item for item in equipment_items
            if normalize_category_key(item["Category"]) in scope
        ]
        items = sorted(items, key=lambda item: str(item["context"]["name"]).lower())

        processed_keys.add(key)

        if slug not in seen_category_slugs:
            category_pages.append({"title": title, "slug": slug})
            seen_category_slugs.add(slug)

        # select schema for this category
        import importlib
        schema_mod = None
        try:
            schema_mod = importlib.import_module(f"generator.schemas.{slug}")
        except Exception:
            try:
                schema_mod = importlib.import_module("generator.schemas.default")
            except Exception:
                schema_mod = None

        if schema_mod is not None:
            schema_fields = list(schema_mod.EQUIPMENT_FIELDS.keys())
            rendered_rows = []
            for item in items:
                props = item["properties"]
                ctx = item["context"]
                row = {}
                for field_name, extractor in schema_mod.EQUIPMENT_FIELDS.items():
                    try:
                        row[field_name] = extractor(props, ctx)
                    except Exception:
                        row[field_name] = "—"
                rendered_rows.append(row)
        else:
            schema_fields = default_headers
            rendered_rows = [
                {
                    "Icon": item["context"]["icon"],
                    "Name": item["context"]["name"],
                    "Category": item.get("Category"),
                    "Price": item["properties"].get("ExpectedPrice") or item["properties"].get("Price") or "—",
                }
                for item in items
            ]

        write_page(
            DOCS / f"{slug}.md",
            title=title,
            description=(
                f"{len(rendered_rows)} matching assets in the {title} category."
            ),
            headers=schema_fields,
            rows=rendered_rows,
        )

    write_index_page(DOCS / "index.md", category_pages)

    icons_found = sum(
        item["context"]["icon"] != "—"
        for item in equipment_items
    )

    write_generation_report(
        DOCS / "generation-report.md",
        scanned=scanned,
        generated=len(equipment_items),
        icons_found=icons_found,
    )

    print(
        f"Scanned {scanned}; "
        f"generated {len(equipment_items)} equipment items; "
        f"icons {icons_found}."
    )


if __name__ == "__main__":
    main()