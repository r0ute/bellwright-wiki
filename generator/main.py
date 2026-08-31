from pathlib import Path

from . import icon, renderer
from .equipment import generator as equipment_generator

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
ASSETS = ROOT / "assets"
ICON_OUT = DOCS / "assets" / "icons"


def clean_output() -> None:
    """Remove generated documentation and icons."""
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

    equipment_pages = equipment_generator.generate(
        ASSETS,
        DOCS,
        ICON_OUT,
        icon_index,
    )

    renderer.write_index_page(
        DOCS / "index.md",
        equipment_pages,
        ASSETS / "T_Logo.webp",
    )


if __name__ == "__main__":
    main()
