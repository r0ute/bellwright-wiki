"""Render quest trees to Markdown."""

from pathlib import Path

from .model import QuestNode


def _write_quest_page(path: Path, quest_name: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "---",
                "layout: default",
                f"title: {quest_name}",
                "---",
                "",
                f"# {quest_name}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_index(path: Path, title: str, links: list[tuple[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "layout: default",
        f"title: {title}",
        "---",
        "",
        f"# {title}",
        "",
    ]
    lines.extend(f"- [{name}]({link})" for name, link in links)
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _render_node(node: QuestNode, directory: Path) -> None:
    links = []

    for key, child in sorted(
        node.children.items(),
        key=lambda item: item[1].name.casefold(),
    ):
        child_directory = directory / key
        _render_node(child, child_directory)
        links.append((child.name, f"{key}/"))

    if node.quest is not None:
        _write_quest_page(directory / "index.md", node.quest.name)

    if links:
        _write_index(directory / "index.md", node.name, links)


def write_category(
    docs: Path,
    category_slug: str,
    tree: QuestNode,
    quests: list,
) -> None:
    """Write the category tree and its category Markdown entry point."""
    directory = docs / category_slug
    directory.mkdir(parents=True, exist_ok=True)

    _render_node(tree, directory)

    links = []
    for key, child in sorted(
        tree.children.items(),
        key=lambda item: item[1].name.casefold(),
    ):
        links.append((child.name, f"{category_slug}/{key}/"))

    _write_index(
        docs / f"{category_slug}.md",
        tree.name,
        links,
    )
