import importlib
import json
from pathlib import Path

from generator import markdown as md
from generator import renderer, scanner


def main() -> None:
    ASSETS = scanner.ASSETS
    DOCS = scanner.DOCS
    ICON_OUT = scanner.ICON_OUT

    DOCS.mkdir(parents=True, exist_ok=True)
    for stale in DOCS.glob("*.md"):
        stale.unlink()

    print(f"Assets: {ASSETS}")
    print(f"Docs:   {DOCS}")

    icon_index = scanner.build_icon_index(ASSETS)
    category_index = scanner.build_category_index(ASSETS)

    print(f"Icons indexed: {len(icon_index)}")
    print(f"Categories indexed: {len(category_index)}")

    equipment_items = []
    equipment_raw = []
    scanned = 0
    category_pages: list[dict] = []
    seen_category_slugs: set[str] = set()

    for path in scanner.discover_json(ASSETS):
        scanned += 1

        if not scanner.is_equipment_item_path(path):
            continue

        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"SKIP {path}: {exc}")
            continue

        if not isinstance(raw, list):
            raw = [raw]

        cdo = scanner.find_cdo(raw)
        if not cdo:
            continue

        props = cdo.get("Properties", {})
        equipment_raw.append((path, props))

        equipment_items.append(
            scanner.generate_equipment_item(
                path,
                raw,
                icon_index,
                category_index,
            )
        )

    default_headers = ["Icon", "Name", "Category", "Price"]
    category_children, category_titles = scanner.build_category_hierarchy(ASSETS)

    # No automatic schema generation: rely on existing schema modules in generator/schemas
    # and fall back to generator/schemas/default.py at render time.

    # Now build pages (groups first, then singles)
    category_paths = list(scanner.equipment_category_paths(ASSETS))

    path_by_key: dict[str, Path] = {}
    for path in category_paths:
        title = scanner.category_name_for_path(path)
        if not title:
            continue
        path_by_key[scanner.normalize_category_key(title)] = path

    processed_keys: set[str] = set()

    # Phase 1: groups
    for path in sorted(category_paths, key=lambda p: str(p).lower()):
        if not scanner.is_equipment_category_group(path):
            continue

        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue

        objects = raw if isinstance(raw, list) else [raw]
        cdo = scanner.find_cdo(objects)
        if not cdo:
            continue

        title = scanner.asset_name(path, objects)
        key = scanner.normalize_category_key(title)
        if key in processed_keys:
            continue

        slug = scanner.category_slug(path.stem)

        sections: dict[str, tuple[list[str], list[dict]]] = {}

        child_keys = sorted(
            category_children.get(key, set()), key=lambda k: category_titles.get(k, "")
        )

        if child_keys:
            for child_key in child_keys:
                child_title = category_titles.get(child_key)
                if not child_title:
                    continue

                child_path = path_by_key.get(child_key)
                if child_path and scanner.is_equipment_category_group(child_path):
                    continue

                child_scope = scanner.category_row_scope(
                    child_title, category_children, category_titles
                )
                child_items = [
                    item
                    for item in equipment_items
                    if scanner.normalize_category_key(item["Category"]) in child_scope
                ]

                # select schema: prefer child-specific, then group schema, then default
                schema = None
                child_slug = None
                if child_path:
                    child_slug = scanner.category_slug(child_path.stem)
                    try:
                        schema = importlib.import_module(
                            f"generator.schemas.{child_slug}"
                        )
                    except Exception:
                        schema = None

                if schema is None:
                    # try the group's schema (slug)
                    try:
                        schema = importlib.import_module(f"generator.schemas.{slug}")
                    except Exception:
                        schema = None

                if schema is None:
                    schema = importlib.import_module("generator.schemas.default")

                schema_fields = list(schema.EQUIPMENT_FIELDS.keys())
                rendered_rows = []
                for item in child_items:
                    props = item["properties"]
                    ctx = item["context"]
                    row = {}
                    for field_name, extractor in schema.EQUIPMENT_FIELDS.items():
                        try:
                            row[field_name] = extractor(props, ctx)
                        except Exception:
                            row[field_name] = ""
                    rendered_rows.append(row)

                rendered_rows = sorted(
                    rendered_rows, key=lambda r: str(r.get("Name", "")).lower()
                )
                sections[child_title] = (schema_fields, rendered_rows)
                processed_keys.add(child_key)

            processed_keys.add(key)
        else:
            group_scope = scanner.category_row_scope(
                title, category_children, category_titles
            )
            group_items = [
                item
                for item in equipment_items
                if scanner.normalize_category_key(item["Category"]) in group_scope
            ]

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
                            row[field_name] = ""
                else:
                    row["Icon"] = ctx["icon"]
                    row["Name"] = ctx["name"]
                    row["Category"] = item.get("Category")
                    row["Price"] = (
                        props.get("ExpectedPrice") or props.get("Price") or ""
                    )

                rendered_rows.append(row)

            rendered_rows = sorted(
                rendered_rows, key=lambda r: str(r.get("Name", "")).lower()
            )
            sections[title] = (schema_fields, rendered_rows)
            processed_keys.add(key)

        total = sum(len(r) for _, r in sections.values())
        if slug not in seen_category_slugs:
            category_pages.append({"title": title, "slug": slug})
            seen_category_slugs.add(slug)

        md.write_page(
            DOCS / f"{slug}.md",
            title=title,
            description=(f"{total} matching assets."),
            headers=default_headers,
            sections=sections,
        )

    # Phase 2
    for path in sorted(category_paths, key=lambda p: str(p).lower()):
        if scanner.is_equipment_category_group(path):
            continue

        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue

        objects = raw if isinstance(raw, list) else [raw]
        cdo = scanner.find_cdo(objects)
        if not cdo:
            continue

        title = scanner.asset_name(path, objects)
        key = scanner.normalize_category_key(title)
        if key in processed_keys:
            continue

        slug = scanner.category_slug(path.stem)
        scope = scanner.category_row_scope(title, category_children, category_titles)
        items = [
            item
            for item in equipment_items
            if scanner.normalize_category_key(item["Category"]) in scope
        ]
        items = sorted(items, key=lambda item: str(item["context"]["name"]).lower())

        processed_keys.add(key)

        if slug not in seen_category_slugs:
            category_pages.append({"title": title, "slug": slug})
            seen_category_slugs.add(slug)

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
                        row[field_name] = ""
                rendered_rows.append(row)
        else:
            schema_fields = default_headers
            rendered_rows = [
                {
                    "Icon": item["context"]["icon"],
                    "Name": item["context"]["name"],
                    "Category": item.get("Category"),
                    "Price": item["properties"].get("ExpectedPrice")
                    or item["properties"].get("Price")
                    or "",
                }
                for item in items
            ]

        md.write_page(
            DOCS / f"{slug}.md",
            title=title,
            description=(f"{len(rendered_rows)} matching assets."),
            headers=schema_fields,
            rows=rendered_rows,
        )

    renderer.write_index_page(DOCS / "index.md", category_pages)

    icons_found = sum(item["context"]["icon"] != "" for item in equipment_items)

    md.write_generation_report(
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
