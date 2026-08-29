from pathlib import Path


def write_index_page(output: Path, categories: list[dict]) -> None:
    """
    Write the root documentation index.

    Equipment is represented by index.md and is never emitted as
    equipment.md. The supplied categories are the child groups:
        Ammo, Armors, Clothing, Gear, Tools, Weapons
    """
    lines = [
        "---",
        "layout: default",
        "title: Bellwright Data",
        "---",
        "",
        "# Bellwright Data",
        "",
        "A searchable reference of extracted **Bellwright** game data, "
        "including equipment, categories, properties, and item icons.",
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

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
