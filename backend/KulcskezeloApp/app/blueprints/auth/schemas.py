from marshmallow import Schema
from apiflask.fields import String, Integer
from apiflask.validators import Email


class UserLoginSchema(Schema):
    email = String(required=True, validate=Email())
    password = String(required=True)


class RegisterRequestSchema(Schema):
    name = String(required=True)
    email = String(required=True, validate=Email())
    password = String(required=True)
    role = String(load_default="Instructor")
    pin = String(load_default=None)


class UserResponseSchema(Schema):
    id = Integer()
    name = String()
    email = String()
    token = String()


class TokenResponseSchema(Schema):
    token = String()
    user_id = Integer()
