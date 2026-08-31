"""Data models used by the quest generator."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Quest:
    name: str
    category: str
    source: Path
    relative_path: tuple[str, ...]


@dataclass
class QuestNode:
    name: str
    quest: Quest | None = None
    children: dict[str, "QuestNode"] = field(default_factory=dict)
