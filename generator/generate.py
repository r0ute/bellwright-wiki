from pathlib import Path
import json

from categories import category_from_path
from discover import discover_json
from icons import build_icon_index, copy_icon, find_icon
from markdown import write_generation_report, write_weapons


ROOT = Path(__file__).resolve().parent.parent

ASSETS = ROOT / "assets"
DOCS = ROOT / "docs"

ICON_OUT = DOCS / "assets" / "icons"


def value(properties: dict, key: str):
    value = properties.get(key)

    if isinstance(value, dict):
        return (
            value.get("LocalizedString")
            or value.get("SourceString")
            or value.get("AssetPathName")
            or value.get("ObjectName")
        )

    return value


def asset_name(path: Path, objects: list) -> str:
    properties = next(
        (
            obj.get("Properties")
            for obj in objects
            if isinstance(obj, dict)
            and isinstance(obj.get("Properties"), dict)
        ),
        {},
    )

    name = properties.get("Name")

    if isinstance(name, dict):
        return (
            name.get("LocalizedString")
            or name.get("SourceString")
            or path.stem
        )

    if isinstance(name, str) and name:
        return name

    return path.stem


def find_cdo(objects: list) -> dict | None:
    """
    FModel exports commonly contain BlueprintGeneratedClass + CDO.

    Select the object containing Properties.
    """
    return next(
        (
            obj
            for obj in objects
            if isinstance(obj, dict)
            and isinstance(obj.get("Properties"), dict)
        ),
        None,
    )


def weapon_strength(properties: dict):
    requirements = properties.get("SkillRequirements", [])

    if not isinstance(requirements, list):
        return "—"

    for requirement in requirements:
        if not isinstance(requirement, dict):
            continue

        if "Strength" in str(requirement.get("Key", "")):
            return requirement.get("Value", "—")

    return "—"


def weapon_type(properties: dict):
    weapon_type = properties.get("WeaponType")

    if isinstance(weapon_type, dict):
        asset_path = weapon_type.get("AssetPathName", "")

        if asset_path:
            return Path(asset_path.split(".")[0]).name

        return weapon_type.get("ObjectName", "—")

    return weapon_type or "—"


def generate_weapon(
    path: Path,
    objects: list,
    icon_index: dict[str, Path],
) -> dict:
    properties = find_cdo(objects)["Properties"]

    name = asset_name(path, objects)

    icon = find_icon(properties, icon_index)

    icon_md = "—"

    if icon:
        destination = copy_icon(icon, ICON_OUT)
        icon_md = (
            f'<img src="assets/icons/{destination.name}" '
            f'alt="{name}" width="48">'
        )

    return {
        "Icon": icon_md,
        "Name": name,
        "Type": weapon_type(properties),
        "Tier": value(properties, "Tier") or "—",
        "Damage": value(properties, "Damage") or "—",
        "Thrust": value(properties, "ThrustDamage") or "—",
        "Speed": value(properties, "WeaponSpeed") or "—",
        "Impact": value(properties, "Impact") or "—",
        "Stability": value(properties, "Stability") or "—",
        "Length": value(properties, "WeaponLength") or "—",
        "Max Durability": (
            value(properties, "MaxDurability")
            or value(properties, "Durability")
            or "—"
        ),
        "Price": (
            value(properties, "ExpectedPrice")
            or value(properties, "Price")
            or "—"
        ),
        "Strength": weapon_strength(properties),
        "Source": str(path.relative_to(ASSETS)).replace("\\", "/"),
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

        category = category_from_path(path)

        if category != "weapons":
            continue

        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"SKIP {path}: {exc}")
            continue

        if not isinstance(raw, list):
            raw = [raw]

        cdo = find_cdo(raw)

        if not cdo:
            continue

        weapons.append(
            generate_weapon(
                path,
                raw,
                icon_index,
            )
        )

    write_weapons(
        weapons,
        DOCS / "weapons.md",
    )

    icons_found = sum(
        1
        for weapon in weapons
        if weapon["Icon"] != "—"
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