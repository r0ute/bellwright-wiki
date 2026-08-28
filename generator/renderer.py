from pathlib import Path


def write_index_page(output: Path, categories: list[dict]) -> None:
    lines = [
        "---",
        "layout: default",
        "title: Bellwright Data",
        "---",
        "",
        "# Bellwright Data",
        "",
        "## Categories",
        "",
    ]

    for category in sorted(categories, key=lambda item: item["title"].lower()):
        lines.append(
            f'- [{category["title"]}]({category["slug"]})'
        )

    lines.extend([
        "",
        "## Reports",
        "",
        "- [Generation report](generation-report)",
        "",
    ])

    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
