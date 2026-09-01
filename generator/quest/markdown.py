"""Render quest documentation to Markdown."""

from pathlib import Path

from .model import Quest, QuestItem, QuestNode, QuestReward, QuestStep


def _format_items(items: tuple[QuestItem, ...]) -> str:
    values = []

    for item in items:
        if item.min_amount == item.max_amount:
            amount = str(item.min_amount)
        else:
            amount = f"{item.min_amount}-{item.max_amount}"

        values.append(f"{item.name} x {amount}")

    return ", ".join(values)


def _format_reward(reward: QuestReward) -> str:
    value = reward.name

    if reward.min_amount is not None and reward.max_amount is not None:
        if reward.min_amount == reward.max_amount:
            amount = str(reward.min_amount)
        else:
            amount = f"{reward.min_amount}-{reward.max_amount}"

        value = f"{value} x {amount}"

    if reward.chance is not None:
        chance = f"{reward.chance * 100:g}%"

        if reward.per_roll:
            chance += "/roll"

        value = f"{value} ({chance})"

    return value


def _format_rewards(
    rewards: tuple[QuestReward, ...],
) -> tuple[list[str], list[str]]:
    guaranteed = []
    random = []

    for reward in rewards:
        value = _format_reward(reward)

        if reward.chance is None:
            guaranteed.append(value)
        else:
            random.append(value)

    return guaranteed, random


def _write_rewards(
    lines: list[str],
    quest: Quest,
) -> None:
    if (
        quest.village_trust_reward <= 0
        and quest.money_reward <= 0
        and quest.renown_reward <= 0
        and not quest.rewards
    ):
        return

    lines.extend(
        [
            "## Rewards",
            "",
        ]
    )

    guaranteed = []

    if quest.village_trust_reward > 0:
        guaranteed.append(f"Village Trust x {quest.village_trust_reward}")

    if quest.money_reward > 0:
        guaranteed.append(f"Money x {quest.money_reward}")

    if quest.renown_reward > 0:
        guaranteed.append(f"Renown x {quest.renown_reward}")

    reward_guaranteed, random = _format_rewards(quest.rewards)

    guaranteed.extend(reward_guaranteed)

    if guaranteed:
        lines.extend(
            [
                f"- {', '.join(guaranteed)}",
                "",
            ]
        )

    if random:
        lines.extend(
            [
                "### Random",
                f"- {', '.join(random)}",
                "",
            ]
        )


def _write_step_content(
    lines: list[str],
    step: QuestStep,
) -> None:
    if step.summary:
        lines.extend(
            [
                step.summary,
                "",
            ]
        )

    if step.items:
        lines.extend(
            [
                f"**Items to bring:** {_format_items(step.items)}",
                "",
            ]
        )


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

    _write_step_content(lines, step)


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

    _write_rewards(
        lines,
        quest,
    )

    path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def _write_page(
    path: Path,
    title: str,
    lines: list[str],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    content = [
        "---",
        "layout: default",
        f"title: {title}",
        "---",
        "",
        f"# {title}",
        "",
        *lines,
        "",
    ]

    path.write_text(
        "\n".join(content),
        encoding="utf-8",
    )


def _write_directory(
    node: QuestNode,
    directory: Path,
) -> None:
    """Write quest pages while using tree nodes as directories."""
    if node.quest is not None:
        _write_quest_page(
            directory.with_suffix(".md"),
            node.quest,
        )

    if not node.children:
        return

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    for key, child in sorted(
        node.children.items(),
        key=lambda item: item[1].name.casefold(),
    ):
        _write_directory(
            child,
            directory / key,
        )


def _write_tree(
    lines: list[str],
    node: QuestNode,
    prefix: str = "",
    indent: int = 0,
) -> None:
    for key, child in sorted(
        node.children.items(),
        key=lambda item: item[1].name.casefold(),
    ):
        padding = "  " * indent

        if child.quest is not None:
            lines.append(f"{padding}- [{child.name}]({prefix}{key}.md)")
        else:
            lines.append(f"{padding}- {child.name}")

            _write_tree(
                lines,
                child,
                f"{prefix}{key}/",
                indent + 1,
            )


def write_category(
    docs: Path,
    category_slug: str,
    tree: QuestNode,
) -> None:
    """Write a quest category."""

    directory = docs / category_slug

    _write_directory(
        tree,
        directory,
    )

    index_lines: list[str] = []

    _write_tree(
        index_lines,
        tree,
        f"{category_slug}/",
    )

    _write_page(
        docs / f"{category_slug}.md",
        tree.name,
        index_lines,
    )


def write_root(
    docs: Path,
    categories: list[tuple[str, str]],
) -> None:
    """Write the root quest page."""

    lines = [f"- [{title}]({slug}.md)" for title, slug in categories]

    _write_page(
        docs / "quest.md",
        "Quests",
        lines,
    )
