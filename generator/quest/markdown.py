"""Render quest documentation to Markdown."""

from pathlib import Path

from .model import Quest, QuestNode


def _write_quest_page(path: Path, quest: Quest) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "---",
        "layout: default",
        f"title: {quest.title}",
        "---",
        "",
        f"# {quest.title}",
        "",
    ]

    if quest.summary:
        lines.extend(
            [
                quest.summary,
                "",
            ]
        )

    if quest.steps:
        lines.extend(
            [
                "## Steps",
                "",
            ]
        )

        for index, step in enumerate(quest.steps, start=1):
            lines.extend(
                [
                    f"### {index}. {step.name}",
                    "",
                ]
            )

            if step.summary:
                lines.extend(
                    [
                        step.summary,
                        "",
                    ]
                )

    path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def _write_index(
    path: Path,
    title: str,
    links: list[tuple[str, str]],
) -> None:
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

    path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def _write_directory(
    node: QuestNode,
    directory: Path,
) -> None:
    directory.mkdir(parents=True, exist_ok=True)

    if node.quest is not None:
        _write_quest_page(
            directory / "index.md",
            node.quest,
        )

    links = []

    for key, child in sorted(
        node.children.items(),
        key=lambda item: item[1].name.casefold(),
    ):
        child_directory = directory / key

        _write_directory(
            child,
            child_directory,
        )

        links.append(
            (
                child.name,
                f"{key}/",
            )
        )

    if node.quest is None:
        _write_index(
            directory / "index.md",
            node.name,
            links,
        )


def write_category(
    docs: Path,
    category_slug: str,
    tree: QuestNode,
) -> None:
    """Write a quest category."""

    directory = docs / category_slug
    directory.mkdir(parents=True, exist_ok=True)

    _write_directory(
        tree,
        directory,
    )

    links = []

    for key, child in sorted(
        tree.children.items(),
        key=lambda item: item[1].name.casefold(),
    ):
        links.append(
            (
                child.name,
                f"{key}/",
            )
        )

    _write_index(
        directory / "index.md",
        tree.name,
        links,
    )
