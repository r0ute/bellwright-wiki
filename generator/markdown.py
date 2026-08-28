from pathlib import Path


def markdown_value(value) -> str:
    if value is None:
        return "—"

    return str(value).replace("|", r"\|").replace("\n", " ")


def render_table(
    rows: list[dict],
    headers: list[str],
) -> list[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| "
        + " | ".join(
            ["---"] * 3 + ["---:"] * (len(headers) - 3)
        )
        + " |",
    ]

    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                markdown_value(row.get(header, "—"))
                for header in headers
            )
            + " |"
        )

    return lines


def render_page(
    title: str,
    description: str,
    rows: list[dict],
    headers: list[str],
) -> str:
    lines = [
        "---",
        "layout: default",
        f"title: {title}",
        "---",
        "",
        f"# {title}",
        "",
        f"*{description}*",
        "",
        '<input class="table-search" type="search" '
        f'placeholder="Search {title.lower()}...">',
        "",
        *render_table(rows, headers),
        "",
    ]

    return "\n".join(lines)


def write_page(
    output: Path,
    title: str,
    description: str,
    rows: list[dict],
    headers: list[str],
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)

    output.write_text(
        render_page(
            title,
            description,
            rows,
            headers,
        ),
        encoding="utf-8",
    )


def write_generation_report(
    output: Path,
    scanned: int,
    generated: int,
    icons_found: int,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)

    output.write_text(
        "# Generation Report\n\n"
        f"- JSON files scanned: {scanned}\n"
        f"- Weapon CDOs generated: {generated}\n"
        f"- Icons found: {icons_found}\n\n"
        "The generator processes every JSON whose path contains "
        "an exact `Weapons` directory. "
        "It does not filter by tier, rarity, or weapon type.\n",
        encoding="utf-8",
    )