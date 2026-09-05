from __future__ import annotations

import json
from pathlib import Path

from ..navigation import breadcrumb_include, navigation_metadata


def markdown_value(value):
    if value is None:
        return ""
    return str(value).replace("|", r"\|").replace("\n", " ")


def render_table(rows, headers):
    if not headers:
        return []
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    lines += [
        "| " + " | ".join(markdown_value(row.get(h, "")) for h in headers) + " |"
        for row in rows
    ]
    return lines


def render_page(
    title,
    *,
    rows=None,
    headers=None,
    links=None,
    parent=None,
    parent_path=None,
    grand_parent=None,
    grand_parent_path=None,
):
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
        *breadcrumb_include(),
        f"# {title}",
        "",
    ]
    if links:
        lines += [f"- [{t}]({u})" for t, u in links] + [""]
    if rows is not None and headers:
        lines += render_table(rows, headers) + [""]
    return "\n".join(lines)


def write_page(
    output: Path,
    title: str,
    *,
    rows=None,
    headers=None,
    links=None,
    parent=None,
    parent_path=None,
    grand_parent=None,
    grand_parent_path=None,
):
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        render_page(
            title,
            rows=rows,
            headers=headers,
            links=links,
            parent=parent,
            parent_path=parent_path,
            grand_parent=grand_parent,
            grand_parent_path=grand_parent_path,
        ),
        encoding="utf-8",
    )
