import json
from pathlib import Path

from ..navigation import breadcrumb_include, navigation_metadata


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
    rows: list[dict] | None = None,
    headers: list[str] | None = None,
    sections: dict[str, tuple[list[str], list[dict]]] | None = None,
    links: list[tuple[str, str]] | None = None,
    parent: str | None = None,
    parent_path: str | None = None,
    grand_parent: str | None = None,
    grand_parent_path: str | None = None,
) -> str:
    """Render a complete Markdown page."""
    headers = headers or []

    lines = [
        "---",
        "layout: default",
        f"title: {json.dumps(title)}",
        *navigation_metadata(
            parent=parent,
            parent_path=parent_path,
            grand_parent=grand_parent,
            grand_parent_path=grand_parent_path,
        ),
        "---",
        "",
        *breadcrumb_include(),
        f"# {title}",
        "",
    ]

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
            rows=rows,
            headers=headers,
            sections=sections,
            links=links,
        ),
        encoding="utf-8",
    )
