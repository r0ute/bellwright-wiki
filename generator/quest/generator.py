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
    quests_by_category = discover_quests(assets, QUEST_CATEGORIES)
    quest_docs = docs / "quest"
    quest_docs.mkdir(parents=True, exist_ok=True)

    print(f"Quest categories processed: {len(QUEST_CATEGORIES)}")

    pages = []

    for category, slug in QUEST_CATEGORIES.items():
        quests = quests_by_category[category]
        tree = build_tree(category, quests)
        write_category(
            quest_docs,
            slug,
            tree,
            quests,
        )

        print(f"\tGENERATED quest/{slug}.md ({len(quests)} items)")

        pages.append(
            {
                "title": category,
                "slug": f"quest/{slug}.md",
            }
        )

    return {
        "title": TITLE,
        "pages": pages,
    }
