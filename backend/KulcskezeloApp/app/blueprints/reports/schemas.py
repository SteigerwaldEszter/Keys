from apiflask import Schema
from apiflask.fields import DateTime, Integer, String


class UsageReportSchema(Schema):
    total_keys = Integer()
    handed_out_keys = Integer()
    available_keys = Integer()


class MissingKeySchema(Schema):
    key_id = Integer()
    room_id = String()
    reservation_id = Integer()
    end_time = DateTime()
    handler_id = Integer()


class AuditLogOutSchema(Schema):
    id = Integer()
    user_id = Integer(allow_none=True)
    action = String()
    entity_name = String()
    entity_value = String(allow_none=True)
    old_value = String(allow_none=True)
    new_value = String(allow_none=True)
    timestamp = DateTime()
