from pathlib import Path

from generator.icon import copy_icon


def _render_group(group: dict) -> list[str]:
    lines = [
        '<div class="data-group" markdown="1">',
        "",
        f"## {group['title']}",
        "",
    ]

    lines.extend(f"- [{page['title']}]({page['slug']})" for page in group["pages"])

    lines.extend(
        [
            "",
            "</div>",
            "",
        ]
    )

    return lines


def _render_data(page_groups: list[dict]) -> list[str]:
    lines = []

    for group in page_groups:
        lines.extend(_render_group(group))

    return lines


def write_index_page(
    output: Path,
    page_groups: list[dict],
    logo: Path,
) -> None:
    """Write the root documentation index."""
    output.parent.mkdir(parents=True, exist_ok=True)

    logo_path = copy_icon(
        logo,
        output.parent / "assets",
    )

    logo_src = logo_path.relative_to(output.parent).as_posix()

    lines = [
        "---",
        "layout: default",
        "title: Bellwright Data",
        "---",
        "",
        (
            f'<p align="center" class="logo"><img src="{logo_src}" '
            'alt="Bellwright" width="96"></p>'
        ),
        "",
        "# Bellwright Data",
        "",
        (
            "A searchable reference of **Bellwright** game data, "
            "organized for easy browsing."
        ),
        "",
        (
            "[![GitHub](https://img.shields.io/badge/"
            "Source%20Code-GitHub-181717?logo=github)]"
            "(https://github.com/r0ute/bw-data)"
        ),
        "",
        *_render_data(page_groups),
    ]

    output.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )
