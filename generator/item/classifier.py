from __future__ import annotations

from pathlib import Path


def source_family(path: Path) -> str:
    parts = list(path.parts)
    lower = [p.lower() for p in parts]
    try:
        i = lower.index("items")
    except ValueError:
        return ""
    return parts[i + 1] if i + 1 < len(parts) else ""
