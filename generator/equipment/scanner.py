"""Backward-compatible scanner aliases."""

from ..item.scanner import (
    discover_paths as discover_items,
    find_cdo,
    load_cdo,
    load_objects,
    load_properties,
)

__all__ = [
    "discover_items",
    "find_cdo",
    "load_cdo",
    "load_objects",
    "load_properties",
]
