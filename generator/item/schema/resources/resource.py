from ..common import BASE_FIELDS, FieldExtractor, field

FIELDS: dict[str, FieldExtractor] = dict(BASE_FIELDS)
FIELDS.update({
    "Volume": field("Volume"),
    "Mesh": field("Mesh"),
    "Carry Animation": field("CarryAnimTypeOverride"),
})
RESOURCE_FIELDS = FIELDS
