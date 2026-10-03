from apiflask import Schema
from apiflask.fields import DateTime, Integer, String


class IssueOutSchema(Schema):
    id = Integer()
    room_id = String()
    user_id = Integer()
    title = String()
    description = String()
    status = String()
    created_at = DateTime()


class IssueCreateSchema(Schema):
    room_id = String(required=True)
    title = String(required=True)
    description = String(load_default="")


class IssueUpdateSchema(Schema):
    status = String(required=True)
