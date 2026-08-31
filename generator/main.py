from pathlib import Path

from generator import icon, renderer
from generator.equipment import generator as equipment_generator

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
DOCS = ROOT / "docs"
ICON_OUT = DOCS / "assets" / "icons"


def clean_output() -> None:
    """Remove previously generated documentation and icons."""
    DOCS.mkdir(parents=True, exist_ok=True)

    for path in DOCS.glob("*.md"):
        path.unlink()

    if ICON_OUT.exists():
        for path in ICON_OUT.iterdir():
            if path.is_file():
                path.unlink()


def main() -> None:
    clean_output()

    icon_index = icon.build_icon_index(ASSETS)

    category_pages = equipment_generator.generate(
        ASSETS,
        DOCS,
        ICON_OUT,
        icon_index,
    )

    renderer.write_index_page(
        DOCS / "index.md",
        category_pages,
        ASSETS / "T_Logo.webp",
    )


if __name__ == "__main__":
    main()
