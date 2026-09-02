"""Navigation metadata for generated Jekyll pages."""

import json


def page_url(path: str) -> str:
    """Convert a generated Markdown path to its Jekyll page URL."""
    normalized = path.replace("\\", "/").lstrip("/")

    if normalized == "index.md":
        return "/"

    if normalized.endswith(".md"):
        normalized = normalized[:-3]

    return f"/{normalized}"


def navigation_metadata(
    *,
    parent: str | None = None,
    parent_path: str | None = None,
    grand_parent: str | None = None,
    grand_parent_path: str | None = None,
) -> list[str]:
    """Render parent/grand-parent front-matter fields."""
    lines: list[str] = []

    if parent:
        lines.append(f"parent: {json.dumps(parent)}")

        if parent_path:
            lines.append(f"parent_url: {page_url(parent_path)}")

    if grand_parent:
        lines.append(f"grand_parent: {json.dumps(grand_parent)}")

        if grand_parent_path:
            lines.append(f"grand_parent_url: {page_url(grand_parent_path)}")

    return lines


def breadcrumb_include() -> list[str]:
    """Return the standard breadcrumb include."""
    return [
        "",
        "{% include breadcrumbs.html %}",
        "",
    ]
