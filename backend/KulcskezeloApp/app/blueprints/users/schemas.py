from apiflask.fields import DateTime, Integer, List, Nested, String
from marshmallow import Schema


class UserSchema(Schema):
    id = Integer()
    name = String()
    email = String()
    roles = List(String())
    created_at = DateTime()


class UserListResponseSchema(Schema):
    users = List(Nested(UserSchema))


class RoleUpdateSchema(Schema):
    role_names = List(String(), required=True)
