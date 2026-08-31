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
            title = step.title or step.name

            lines.extend(
                [
                    f"### {index}. {title}",
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

    # The quest belongs to this source directory.
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

    # A directory without a quest gets a normal directory index.
    # A quest directory already has its quest page, so do not overwrite it.
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
    quests: list[Quest],
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
                f"{category_slug}/{key}/",
            )
        )

    _write_index(
        docs / f"{category_slug}.md",
        tree.name,
        links,
    )
