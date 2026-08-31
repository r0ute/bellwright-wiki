"""Build the quest directory tree from source asset paths."""

import re

from .models import Quest, QuestNode


def slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower())
    return value.strip("-")


def build_tree(category: str, quests: list[Quest]) -> QuestNode:
    root = QuestNode(name=category)

    for quest in quests:
        node = root

        # The source directory is authoritative. A quest's references are
        # intentionally ignored so descendants cannot become direct children.
        parts = [*quest.relative_path, quest.name]

        for part in parts:
            key = slugify(part)
            if not key:
                continue
            node = node.children.setdefault(
                key,
                QuestNode(name=part),
            )

        node.quest = quest

    return root
