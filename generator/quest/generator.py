"""Quest documentation generator orchestration."""

from pathlib import Path

from .markdown import write_category
from .scanner import discover_quests
from .tree import build_tree

QUEST_CATEGORIES = {
    "MainQuest": "main-quest",
    "SideQuests": "side-quests",
}

TITLE = "Quests"


def generate(
    assets: Path,
    docs: Path,
    icon_out: Path,
    icon_index: dict,
) -> dict:
    """Generate the configured quest categories."""

    quests_by_category = discover_quests(
        assets,
        QUEST_CATEGORIES,
    )

    print(
        f"Quests indexed: {sum(len(quests) for quests in quests_by_category.values())}"
    )

    quest_docs = docs / "quest"
    quest_docs.mkdir(
        parents=True,
        exist_ok=True,
    )

    pages = []

    for category, slug in QUEST_CATEGORIES.items():
        quests = quests_by_category[category]

        tree = build_tree(
            category,
            quests,
        )

        write_category(
            quest_docs,
            slug,
            tree,
        )

        print(f"\tGENERATED quest/{slug}/index.md ({len(quests)} quests)")

        pages.append(
            {
                "title": category,
                "slug": f"quest/{slug}/",
            }
        )

    return {
        "title": TITLE,
        "pages": pages,
    }
