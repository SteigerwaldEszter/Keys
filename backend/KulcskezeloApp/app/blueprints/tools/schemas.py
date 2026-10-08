from apiflask.fields import Integer, List, Nested, String
from marshmallow import Schema


class ToolSchema(Schema):
    id = Integer()
    name = String()


class ToolListResponseSchema(Schema):
    tools = List(Nested(ToolSchema))


class ToolCreateRequestSchema(Schema):
    name = String(required=True)
