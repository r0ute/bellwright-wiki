from pathlib import Path


def markdown_value(value) -> str:
    """Convert a value to safe Markdown table content."""
    if value is None:
        return ""

    return str(value).replace("|", r"\|").replace("\n", " ")


def render_table(
    rows: list[dict],
    headers: list[str],
) -> list[str]:
    """Render rows as a Markdown table."""
    if not headers:
        return []

    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]

    for row in rows:
        lines.append(
            "| "
            + " | ".join(markdown_value(row.get(header, "")) for header in headers)
            + " |"
        )

    return lines


def render_page(
    title: str,
    description: str,
    rows: list[dict] | None = None,
    headers: list[str] | None = None,
    sections: dict[str, tuple[list[str], list[dict]]] | None = None,
    links: list[tuple[str, str]] | None = None,
) -> str:
    """
    Render a complete Markdown page.

    `sections`:
        {
            "Weapons": (headers, rows),
            "Tools": (headers, rows),
        }

    `links`:
        [
            ("Ammo", "ammo.md"),
            ("Armors", "armors.md"),
        ]
    """
    headers = headers or []

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

    # Optional links, primarily used by index.md.
    if links:
        for link_title, link_target in links:
            lines.append(f"- [{link_title}]({link_target})")

        lines.append("")

    if sections:
        for section_name, section_content in sections.items():
            sec_headers, sec_rows = section_content

            lines.append(f"## {section_name}")
            lines.append("")

            lines.extend(render_table(sec_rows, sec_headers))
            lines.append("")

    elif rows is not None and headers:
        lines.extend(render_table(rows, headers))
        lines.append("")

    return "\n".join(lines)


def write_page(
    output: Path,
    title: str,
    description: str,
    rows: list[dict] | None = None,
    headers: list[str] | None = None,
    sections: dict[str, tuple[list[str], list[dict]]] | None = None,
    links: list[tuple[str, str]] | None = None,
) -> None:
    """Write a rendered Markdown page."""
    output.parent.mkdir(parents=True, exist_ok=True)

    output.write_text(
        render_page(
            title=title,
            description=description,
            rows=rows,
            headers=headers,
            sections=sections,
            links=links,
        ),
        encoding="utf-8",
    )


def write_generation_report(
    output: Path,
    scanned: int,
    generated: int,
    icons_found: int,
) -> None:
    """Write the generation summary."""
    output.parent.mkdir(parents=True, exist_ok=True)

    output.write_text(
        "# Generation Report\n\n"
        f"- JSON files scanned: {scanned}\n"
        f"- Equipment CDOs generated: {generated}\n"
        f"- Icons found: {icons_found}\n",
        encoding="utf-8",
    )
