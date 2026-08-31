from pathlib import Path

from generator.icon import copy_icon


def _index_lines(equipment_pages: list[dict], logo_src: str) -> list[str]:
    lines = [
        "---",
        "layout: default",
        "title: Bellwright Data",
        "---",
        "",
        f'<p align="center" class="logo"><img src="{logo_src}" alt="Bellwright"',
        'width="96"></p>',
        "",
        "# Bellwright Data",
        "",
        "A searchable reference of **Bellwright** game data, "
        "organized for easy browsing.",
        "",
        "[![GitHub](https://img.shields.io/badge/Source%20Code-GitHub-181717?logo=github)]"
        "(https://github.com/r0ute/bw-data)",
        "",
        "## Equipment",
        "",
    ]

    lines.extend(
        f"- [{page['title']}]({page['slug']})"
        for page in sorted(
            equipment_pages,
            key=lambda page: page["title"].lower(),
        )
    )

    return lines


def write_index_page(
    output: Path,
    equipment_pages: list[dict],
    logo: Path,
) -> None:
    """Write the root documentation index."""
    output.parent.mkdir(parents=True, exist_ok=True)

    logo_path = copy_icon(
        logo,
        output.parent / "assets",
    )

    logo_src = logo_path.relative_to(output.parent).as_posix()

    output.write_text(
        "\n".join(
            _index_lines(
                equipment_pages,
                logo_src,
            )
        ),
        encoding="utf-8",
    )
