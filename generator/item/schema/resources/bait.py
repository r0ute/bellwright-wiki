from .resource import FIELDS as RESOURCE_FIELDS
from ..common import FieldExtractor, field

FIELDS: dict[str, FieldExtractor] = dict(RESOURCE_FIELDS)
FIELDS["Bait Type"] = field("BaitType")
BAIT_FIELDS = FIELDS
