"""Quest documentation generator orchestration."""

from pathlib import Path

from .markdown import write_category, write_root
from .scanner import discover_quests
from .tree import build_tree

TITLE = "Quests"


def generate(
    assets: Path,
    docs: Path,
    icon_out: Path,
    icon_index: dict,
) -> dict:
    """Generate all discovered quest categories."""
    quests_by_category = discover_quests(assets)

    print(
        f"Quests indexed: {sum(len(quests) for quests in quests_by_category.values())}"
    )

    quest_docs = docs / "quest"
    quest_docs.mkdir(
        parents=True,
        exist_ok=True,
    )

    pages = []
    categories = []

    for category in quests_by_category:
        slug = category.lower()
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

        print(f"\tGENERATED quest/{slug}.md ({len(quests)} quests)")

        categories.append(
            (
                category,
                slug,
            )
        )

        pages.append(
            {
                "title": category,
                "slug": f"quest/{slug}.md",
            }
        )

    write_root(
        quest_docs,
        sorted(
            categories,
            key=lambda item: item[0].casefold(),
        ),
    )

    return {
        "title": TITLE,
        "pages": pages,
    }
