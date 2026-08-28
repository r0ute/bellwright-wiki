from pathlib import Path


HEADERS = [
    "Icon",
    "Name",
    "Type",
    "Tier",
    "Damage",
    "Thrust",
    "Speed",
    "Impact",
    "Stability",
    "Length",
    "Max Durability",
    "Price",
    "Strength",
]


def markdown_value(value) -> str:
    if value is None:
        return "—"

    value = str(value)

    return value.replace("|", r"\|").replace("\n", " ")


def render_table(rows: list[dict]) -> list[str]:
    lines = [
        "| " + " | ".join(HEADERS) + " |",
        "| " + " | ".join(
            ["---"] * 3 + ["---:"] * (len(HEADERS) - 3)
        ) + " |",
    ]

    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                markdown_value(row.get(header, "—"))
                for header in HEADERS
            )
            + " |"
        )

    return lines


def render_weapons(rows: list[dict]) -> str:
    rows = sorted(
        rows,
        key=lambda row: str(row.get("Name", "")).lower(),
    )

    lines = [
        "---",
        "layout: default",
        "title: All Weapons",
        "---",
        "",
        "# All Weapons",
        "",
        f"*{len(rows)} weapon assets from the raw FModel export.*",
        "",
        '<input class="table-search" type="search" placeholder="Search weapons...">',
        "",
        *render_table(rows),
        "",
    ]

    return "\n".join(lines)


def write_weapons(rows: list[dict], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_weapons(rows), encoding="utf-8")


def write_generation_report(
    output: Path,
    scanned: int,
    generated: int,
    icons_found: int,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)

    text = (
        "# Generation Report\n\n"
        f"- JSON files scanned: {scanned}\n"
        f"- Weapon CDOs generated: {generated}\n"
        f"- Icons found: {icons_found}\n\n"
        "The generator processes every JSON whose path contains "
        "an exact `Weapons` directory. "
        "It does not filter by tier, rarity, or weapon type.\n"
    )

    output.write_text(text, encoding="utf-8")