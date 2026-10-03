from apiflask.fields import Boolean, DateTime, Integer, List, Nested, String
from marshmallow import Schema


class ClassroomFilterSchema(Schema):
    capacity_min = Integer(load_default=0)
    tools = List(String())
    available_from = DateTime()
    available_to = DateTime()
    room_type = String()


class ClassroomSchema(Schema):
    id = String()
    capacity = Integer()
    is_active = Boolean()
    tools = List(String())
    room_type = String()


class ClassroomListResponseSchema(Schema):
    classrooms = List(Nested(ClassroomSchema))


class ToolSchema(Schema):
    id = Integer()
    name = String()
    quantity = Integer()
    active = Boolean()


class ClassroomDetailResponseSchema(Schema):
    id = String()
    capacity = Integer()
    is_active = Boolean()
    room_type = String()
    tools = List(Nested(ToolSchema))


class ClassroomCreateRequestSchema(Schema):
    id = String()
    capacity = Integer(required=True)
    type_id = Integer(required=True)
    tool_ids = List(Integer())


class ClassroomUpdateRequestSchema(Schema):
    capacity = Integer()
    is_active = Boolean()
    room_type_id = Integer()
    tools_ids = List(Integer())
    tool_quantity = List(Integer())
    tool_active = List(Boolean())
