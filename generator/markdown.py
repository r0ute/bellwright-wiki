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
    rows: list[dict] | None = None,
    headers: list[str] | None = None,
    sections: dict[str, list[dict]] | None = None,
) -> str:
    if headers is None:
        headers = []

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
    ]

    if sections:
        for section_name, section_rows in sections.items():
            lines.append(f"## {section_name}")
            lines.append("")
            lines.extend(render_table(section_rows, headers))
            lines.append("")
    else:
        lines.extend(render_table(rows or [], headers))
        lines.append("")

    return "\n".join(lines)


def write_page(
    output: Path,
    title: str,
    description: str,
    rows: list[dict] | None = None,
    headers: list[str] | None = None,
    sections: dict[str, list[dict]] | None = None,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)

    output.write_text(
        render_page(
            title,
            description,
            rows=rows,
            headers=headers,
            sections=sections,
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
        f"- Equipment CDOs generated: {generated}\n"
        f"- Icons found: {icons_found}\n\n"
        "The generator processes equipment items under the main "
        "`Items/Equipment` tree and groups them by the "
        "category metadata in `Items/Categories/Equipment`. "
        "Category definition assets are excluded from the item tables.\n",
        encoding="utf-8",
    )