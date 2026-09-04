from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class Item:
    """Normalized item definition used by the item generator."""

    path: Path
    family: str
    template: str
    category: str
    name: str
    properties: dict[str, Any] = field(default_factory=dict)

    damaged_item: str = ""
    unbroken_parent: str = ""

    @property
    def stem(self) -> str:
        return self.path.stem
