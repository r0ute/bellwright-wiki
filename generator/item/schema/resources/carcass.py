from .resource import FIELDS as RESOURCE_FIELDS
from ..common import FieldExtractor, field, enum_value

FIELDS: dict[str, FieldExtractor] = dict(RESOURCE_FIELDS)
FIELDS["Animal Class"] = field("AnimalClass", transform=enum_value)
CARCASS_FIELDS = FIELDS
