from pathlib import Path

from generator.icon import copy_icon


def write_index_page(output: Path, equipment_pages: list[dict], logo: Path) -> None:
    """
    Write the root documentation index.
    """

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

    for category in sorted(
        equipment_pages,
        key=lambda item: item["title"].lower(),
    ):
        title = category["title"]
        slug = category["slug"]
        lines.append(f"- [{title}]({slug})")

    output.write_text("\n".join(lines), encoding="utf-8")
