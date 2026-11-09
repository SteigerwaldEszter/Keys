from apiflask.fields import (
    Boolean,
    DateTime,
    Integer,
    List,
    Method,
    Nested,
    String,
)
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
    room_type = Method("get_room_type_name")
    room_type_id = Integer(attribute="room_type")
    tools = Method("get_tool_names")

    def get_room_type_name(self, classroom):
        if classroom.types is None:
            return None

        return classroom.types.name

    def get_tool_names(self, classroom):
        return [
            room_tool.tools.name
            for room_tool in classroom.room_tools
            if room_tool.tools is not None and room_tool.active
        ]


class ClassroomListResponseSchema(Schema):
    classrooms = List(Nested(ClassroomSchema))


class ToolSchema(Schema):
    id = Integer(attribute="tool_id")
    name = Method("get_name")
    quantity = Integer()
    active = Boolean()

    def get_name(self, room_tool):
        if room_tool.tools is None:
            return None

        return room_tool.tools.name


class ClassroomDetailResponseSchema(ClassroomSchema):
    tools = List(
        Nested(ToolSchema),
        attribute="room_tools",
    )


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
