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
    entity_name = String()
    entity_id = Integer()
    action = String()
    created_at = DateTime()
    user_id = Integer()
