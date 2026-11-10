from apiflask import Schema
from apiflask.fields import Boolean, Integer, List, Nested, String


class MasterKeyUserRequestSchema(Schema):
    user_id = Integer(required=True)


class MasterKeyRoomRequestSchema(Schema):
    room_id = String(required=True)


class MasterKeyUserSchema(Schema):
    id = Integer()
    name = String()


class MasterKeyRoomSchema(Schema):
    id = String()
    capacity = Integer()


class MasterKeySummarySchema(Schema):
    id = Integer()
    name = String()
    status = String()
    is_master = Boolean()


class MasterKeysListSchema(Schema):
    master_keys = List(Nested(MasterKeySummarySchema))


class MasterKeyDetailsSchema(Schema):
    key_id = Integer()
    name = String()
    status = String()
    users = List(Nested(MasterKeyUserSchema))
    rooms = List(Nested(MasterKeyRoomSchema))


class MasterKeyMessageSchema(Schema):
    message = String()
