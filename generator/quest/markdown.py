"""Render quest documentation to Markdown."""

from pathlib import Path

from .model import Quest, QuestNode, QuestStep


def _write_step(
    lines: list[str],
    number: int,
    step: QuestStep,
) -> None:
    lines.extend(
        [
            f"### {number}. {step.name}",
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


def _write_parallel_steps(
    lines: list[str],
    number: int,
    steps: list[QuestStep],
) -> None:
    lines.extend(
        [
            "{:.quest-parallel}",
            "",
        ]
    )

    for offset, step in enumerate(steps, start=1):
        lines.extend(
            [
                f"- ### {number}.{offset}. {step.name}",
                "",
            ]
        )

        if step.summary:
            lines.extend(
                [
                    f"  {step.summary}",
                    "",
                ]
            )

    lines.append("")


def _write_steps(
    lines: list[str],
    steps: tuple[QuestStep, ...],
) -> None:
    number = 1
    index = 0

    while index < len(steps):
        step = steps[index]

        if not step.group_next:
            _write_step(
                lines,
                number,
                step,
            )
            number += 1
            index += 1
            continue

        group = [step]

        while (
            index + 1 < len(steps)
            and steps[index].group_next
            and steps[index + 1].type == step.type
        ):
            index += 1
            group.append(steps[index])

        _write_parallel_steps(
            lines,
            number,
            group,
        )

        number += 1
        index += 1


def _write_quest_page(
    path: Path,
    quest: Quest,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

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

        _write_steps(
            lines,
            quest.steps,
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
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

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
    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

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
    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

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
