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
    "Repair Value": field("RepairValue"),
    "Activated Mesh": field("ActivatedMesh"),
    "Sheath Mesh": field("SheathMesh"),
    "Carry Type": field("CarryType"),
    "Damage": field("Damage"),
    "Damage Type": field("DamageType"),
    "Thrust Damage": field("ThrustDamage"),
    "Weapon Type": field("WeaponType"),
}