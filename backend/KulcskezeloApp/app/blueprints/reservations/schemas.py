from apiflask import Schema
from apiflask.fields import DateTime, Integer, List, Nested, String


class ReservationSchema(Schema):
    id = Integer()
    user_id = Integer()
    room_id = String()
    start_time = DateTime()
    end_time = DateTime()
    status = String()
    created_at = DateTime()


class ReservationListResponseSchema(Schema):
    reservations = List(Nested(ReservationSchema))


class ReservationCreateRequestSchema(Schema):
    room_id = String(required=True)
    start_time = DateTime(required=True)
    duration_slots = Integer(load_default=1)
    recurring_weeks = Integer(load_default=1)


class ReservationStatusUpdateRequestSchema(Schema):
    status = String(required=True)
