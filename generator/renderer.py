from pathlib import Path

from generator.icons import copy_icon


def write_index_page(output: Path, categories: list[dict], logo: Path) -> None:
    """
    Write the root documentation index.

    Equipment is represented by index.md and is never emitted as
    equipment.md. The supplied categories are the child groups:
        Ammo, Armors, Clothing, Gear, Tools, Weapons
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
        f'<p align="center"><img src="{logo_src}" alt="Bellwright" width="96"></p>',
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
        categories,
        key=lambda item: item["title"].lower(),
    ):
        title = category["title"]
        slug = category["slug"]

        # Equipment itself belongs to index.md, not equipment.md.
        if title.strip().lower() == "equipment":
            continue

        lines.append(f"- [{title}]({slug})")

    output.write_text("\n".join(lines), encoding="utf-8")
