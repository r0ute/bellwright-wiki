"""Data models used by the quest generator."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class QuestStep:
    name: str
    source: Path
    summary: str = ""
    group_next: bool = False
    type: str = ""


@dataclass(frozen=True)
class Quest:
    name: str
    category: str
    source: Path
    relative_path: tuple[str, ...]
    title: str
    summary: str = ""
    steps: tuple[QuestStep, ...] = field(default_factory=tuple)


@dataclass
class QuestNode:
    name: str
    quest: Quest | None = None
    children: dict[str, "QuestNode"] = field(default_factory=dict)
