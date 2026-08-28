from __future__ import annotations
from typing import Any
try:
    from generator.schemas.common import (
        FieldExtractor,
        extract_value,
        field,
    )
except ModuleNotFoundError:
    from schemas.common import (
        FieldExtractor,
        extract_value,
        field,
    )

EQUIPMENT_FIELDS: dict[str, FieldExtractor] = {
    "Icon": lambda _p, ctx: ctx['icon'],
    "Name": lambda _p, ctx: ctx['name'],
    "Mesh When Preparing": field("MeshWhenPreparing"),
    "Projectile Actor": field("ProjectileActor"),
    "Damage": field("Damage"),
    "Damage Type": field("DamageType"),
    "Projectile Damage": field("ProjectileDamage"),
    "Sound Category": field("SoundCategory"),
    "Rarity": field("Rarity"),
    "Tier": field("Tier"),
}