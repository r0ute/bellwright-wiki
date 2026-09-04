from __future__ import annotations

import json
from pathlib import Path

from ..navigation import breadcrumb_include, navigation_metadata


def markdown_value(value: object) -> str:
    if value is None:
        return ""
    return str(value).replace("|", r"\|").replace("\n", " ")


def render_table(rows: list[dict], headers: list[str]) -> list[str]:
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
    sections: dict[str, tuple[list[str], list[dict]]] | None = None,
) -> str:
    lines = [
        "---",
        "layout: default",
        f"title: {json.dumps(title)}",
        "---",
        "",
        *breadcrumb_include(),
        f"# {title}",
        "",
    ]
    for section_name, (headers, rows) in (sections or {}).items():
        if not headers:
            continue
        lines.extend([f"## {section_name}", ""])
        lines.extend(render_table(rows, headers))
        lines.append("")
    return "\n".join(lines)


def write_page(
    output: Path,
    title: str,
    sections: dict[str, tuple[list[str], list[dict]]],
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        render_page(title, sections),
        encoding="utf-8",
    )
