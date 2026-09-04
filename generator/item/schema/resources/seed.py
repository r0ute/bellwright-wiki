from .resource import FIELDS as RESOURCE_FIELDS
from ..common import FieldExtractor, field

FIELDS: dict[str, FieldExtractor] = dict(RESOURCE_FIELDS)
FIELDS.update(
    {
        "Plant": field("Plant"),
        "Seed Count": field("SeedCount"),
    }
)
SEED_FIELDS = FIELDS
