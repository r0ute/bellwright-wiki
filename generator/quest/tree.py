"""Build the quest documentation tree from source asset paths."""

import re

from .model import Quest, QuestNode


def slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower())
    return value.strip("-")


def build_tree(category: str, quests: list[Quest]) -> QuestNode:
    root = QuestNode(name=category)

    for quest in quests:
        node = root

        for part in quest.relative_path:
            key = slugify(part)
            if not key:
                continue

            node = node.children.setdefault(
                key,
                QuestNode(name=part),
            )

        node.quest = quest

    return root
