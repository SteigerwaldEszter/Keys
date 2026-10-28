from apiflask import Schema
from apiflask.fields import Boolean, DateTime, Integer, List, Nested, String


class MaintenanceCreateRequestSchema(Schema):
    room_id = String(required=True)
    start_time = DateTime(required=True)
    end_time = DateTime(required=True)
    confirm_conflicts = Boolean(load_default=False)


class ConflictingReservationSchema(Schema):
    id = Integer()
    room_id = String()
    start_time = String()
    end_time = String()
    status = String()
    user_id = Integer()
    user_name = String(allow_none=True)
    user_email = String(allow_none=True)


class MaintenanceWindowSchema(Schema):
    id = Integer()
    room_id = String()
    start_time = String()
    end_time = String()
    created_by = Integer()
    is_past = Boolean()
    conflicts = List(Nested(ConflictingReservationSchema))


class ReservationUpdateRequestSchema(Schema):
    room_id = String(required=True)
    start_time = DateTime(required=True)
    end_time = DateTime(required=True)


class MaintenanceListResponseSchema(Schema):
    windows = List(Nested(MaintenanceWindowSchema))
