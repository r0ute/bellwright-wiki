from __future__ import annotations

import json
from pathlib import Path

from ..navigation import breadcrumb_include


def markdown_value(value):
    if value is None:
        return ""

    return str(value).replace("|", r"\|").replace("\n", " ")


def render_table(
    rows,
    headers,
):
    if not headers:
        return []

    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]

    lines += [
        "| "
        + " | ".join(
            markdown_value(
                row.get(
                    header,
                    "",
                )
            )
            for header in headers
        )
        + " |"
        for row in rows
    ]

    return lines


def _front_matter(title: str) -> list[str]:
    return [
        "---",
        "layout: default",
        f"title: {json.dumps(title)}",
        "---",
        "",
        *breadcrumb_include(),
    ]


def render_page(
    title,
    *,
    rows=None,
    headers=None,
    links=None,
):
    lines = [
        *_front_matter(title),
        f"# {title}",
        "",
    ]

    if links:
        lines.extend(f"- [{title}]({url})" for title, url in links)

        lines.append("")

    if rows is not None and headers:
        lines.extend(
            render_table(
                rows,
                headers,
            )
        )

        lines.append("")

    return "\n".join(lines)


def write_page(
    output: Path,
    title: str,
    *,
    rows=None,
    headers=None,
    links=None,
):
    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        render_page(
            title,
            rows=rows,
            headers=headers,
            links=links,
        ),
        encoding="utf-8",
    )


def render_tree_page(
    title: str,
    tree: list[str],
) -> str:
    lines = [
        *_front_matter(title),
        f"# {title}",
        "",
        *tree,
        "",
    ]

    return "\n".join(lines)


def write_tree_page(
    output: Path,
    title: str,
    tree: list[str],
):
    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        render_tree_page(
            title,
            tree,
        ),
        encoding="utf-8",
    )
