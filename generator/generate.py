from pathlib import Path
import json

from categories import category_from_path
from discover import discover_json
from icons import build_icon_index, copy_icon, find_icon
from markdown import write_generation_report, write_page
from schemas.weapons import WEAPON_FIELDS


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


def generate_weapon(
    path: Path,
    objects: list,
    icon_index: dict[str, Path],
) -> dict:
    cdo = find_cdo(objects)

    if not cdo:
        raise ValueError(f"No CDO found: {path}")

    properties = cdo["Properties"]

    name = asset_name(path, objects)

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

    return {
        field: extractor(properties, context)
        for field, extractor in WEAPON_FIELDS.items()
    }


def main():
    print(f"Assets: {ASSETS}")
    print(f"Docs:   {DOCS}")

    icon_index = build_icon_index(ASSETS)

    print(f"Icons indexed: {len(icon_index)}")

    weapons = []
    scanned = 0

    for path in discover_json(ASSETS):
        scanned += 1

        if category_from_path(path) != "weapons":
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

        if not find_cdo(raw):
            continue

        weapons.append(
            generate_weapon(
                path,
                raw,
                icon_index,
            )
        )

    headers = list(WEAPON_FIELDS)

    write_page(
        DOCS / "weapons.md",
        title="All Weapons",
        description=(
            f"{len(weapons)} weapon assets "
            "from the raw FModel export."
        ),
        rows=sorted(
            weapons,
            key=lambda row: str(row["Name"]).lower(),
        ),
        headers=headers,
    )

    icons_found = sum(
        weapon["Icon"] != "—"
        for weapon in weapons
    )

    write_generation_report(
        DOCS / "generation-report.md",
        scanned=scanned,
        generated=len(weapons),
        icons_found=icons_found,
    )

    print(
        f"Scanned {scanned}; "
        f"generated {len(weapons)} weapons; "
        f"icons {icons_found}."
    )


if __name__ == "__main__":
    main()