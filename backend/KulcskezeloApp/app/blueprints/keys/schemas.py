from apiflask import Schema
from apiflask.fields import Boolean, Integer, String


class KeyOutSchema(Schema):
    id = Integer()
    room_id = String()
    name = String()
    status = String()
    is_master = Boolean()

class KeyCreateUpdateSchema(Schema):
    room_id = String(required=True)
    name = String(required=True)
    is_master = Boolean(load_default=False)
    status = String(load_default="available")


class KeyIssueSchema(Schema):
    reservation_id = Integer(required=True)
    receiver_id = Integer(required=True)
    format = String(required=True)
    payload = String(required=True)


class KeyReturnSchema(Schema):
    reservation_id = Integer(required=True)
    receiver_id = Integer(required=True)
    format = String(load_default="SIGNATURE")
    payload = String(load_default="RETURNED_OK")