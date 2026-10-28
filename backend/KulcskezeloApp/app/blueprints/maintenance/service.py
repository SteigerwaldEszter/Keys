from datetime import datetime

from apiflask import abort
from sqlalchemy.orm import joinedload

from app.blueprints.reports.service import create_audit_log
from app.extensions import db
from app.models.classroom import Classroom
from app.models.reservation import Reservation

MAINTENANCE_STATUS = "maintenance"
BLOCKING_RESERVATION_STATUSES = ["pending", "active"]
DISPLAY_FORMAT = "%Y-%m-%d %H:%M"


def _iso(value):
    return value.isoformat() if value is not None else None


def serialize_conflict(reservation):
    owner = reservation.users
    return {
        "id": reservation.id,
        "room_id": reservation.room_id,
        "start_time": _iso(reservation.start_time),
        "end_time": _iso(reservation.end_time),
        "status": reservation.status,
        "user_id": reservation.user_id,
        "user_name": owner.name if owner is not None else None,
        "user_email": owner.email if owner is not None else None,
    }


def serialize_window(reservation, conflicts, now):
    return {
        "id": reservation.id,
        "room_id": reservation.room_id,
        "start_time": _iso(reservation.start_time),
        "end_time": _iso(reservation.end_time),
        "created_by": reservation.user_id,
        "is_past": reservation.end_time <= now,
        "conflicts": [serialize_conflict(item) for item in conflicts],
    }


class MaintenanceService:
    @staticmethod
    def describe_window(reservation):
        start = reservation.start_time.strftime(DISPLAY_FORMAT)
        end = reservation.end_time.strftime(DISPLAY_FORMAT)
        return f"{start} – {end}"

    @staticmethod
    def find_overlapping_window(room_id, start_time, end_time):
        """Az első átfedő, karbantartásként megjelölt reservation."""
        return (
            Reservation.query.filter(
                Reservation.room_id == room_id,
                Reservation.status == MAINTENANCE_STATUS,
                Reservation.start_time < end_time,
                Reservation.end_time > start_time,
            )
            .order_by(Reservation.start_time)
            .first()
        )

    @staticmethod
    def find_conflicting_reservations(room_id, start_time, end_time):
        """Az idősávval átfedő normál, aktív vagy függő foglalások."""
        return (
            Reservation.query.options(joinedload(Reservation.users))
            .filter(
                Reservation.room_id == room_id,
                Reservation.status.in_(BLOCKING_RESERVATION_STATUSES),
                Reservation.start_time < end_time,
                Reservation.end_time > start_time,
            )
            .order_by(Reservation.start_time)
            .all()
        )

    @staticmethod
    def list_windows():
        now = datetime.now()
        windows = (
            Reservation.query.filter(Reservation.status == MAINTENANCE_STATUS)
            .order_by(Reservation.start_time)
            .all()
        )
        upcoming = [item for item in windows if item.end_time > now]
        past = [item for item in windows if item.end_time <= now]
        past.reverse()
        result = []

        for reservation in upcoming:
            conflicts = MaintenanceService.find_conflicting_reservations(
                reservation.room_id, reservation.start_time, reservation.end_time
            )
            result.append(serialize_window(reservation, conflicts, now))

        for reservation in past:
            result.append(serialize_window(reservation, [], now))

        return {"windows": result}

    @staticmethod
    def create_window(data, actor_user_id):
        try:
            room_id = data["room_id"].strip()
            start_time = data["start_time"]
            end_time = data["end_time"]
            confirm_conflicts = bool(data.get("confirm_conflicts", False))
            now = datetime.now()

            if start_time.tzinfo is not None or end_time.tzinfo is not None:
                abort(
                    400,
                    message=(
                        "Az időpontokat időzóna nélkül kell megadni "
                        "(pl. 2026-11-02T08:00:00)."
                    ),
                )
            if end_time <= start_time:
                abort(400, message="A karbantartás végének a kezdete után kell lennie.")
            if end_time <= now:
                abort(400, message="A karbantartás nem lehet teljesen a múltban.")
            if db.session.get(Classroom, room_id) is None:
                abort(404, message="A terem nem található.")

            overlapping = MaintenanceService.find_overlapping_window(
                room_id, start_time, end_time
            )
            if overlapping is not None:
                abort(
                    400,
                    message=(
                        f"A(z) {room_id} teremben erre az időszakra már van "
                        "karbantartás kijelölve "
                        f"({MaintenanceService.describe_window(overlapping)})."
                    ),
                )

            conflicts = MaintenanceService.find_conflicting_reservations(
                room_id, start_time, end_time
            )
            if conflicts and not confirm_conflicts:
                abort(
                    409,
                    message=(
                        f"A karbantartás {len(conflicts)} meglévő foglalással ütközik. "
                        "Az idősáv csak akkor jelölhető ki, ha ezt tudomásul veszed; "
                        "az érintett foglalásokat ezután kezelni kell "
                        "(törlés vagy áthelyezés)."
                    ),
                    detail={
                        "conflicts": [serialize_conflict(item) for item in conflicts]
                    },
                )

            reservation = Reservation(
                room_id=room_id,
                start_time=start_time,
                end_time=end_time,
                status=MAINTENANCE_STATUS,
                user_id=actor_user_id,
            )
            db.session.add(reservation)
            db.session.flush()

            create_audit_log(
                action="MAINTENANCE_CREATED",
                entity_name="reservations",
                entity_value=reservation.id,
                user_id=actor_user_id,
                new_value={
                    "status": MAINTENANCE_STATUS,
                    "room_id": reservation.room_id,
                    "start_time": reservation.start_time,
                    "end_time": reservation.end_time,
                    "conflicts_acknowledged": bool(conflicts),
                    "conflicting_reservation_ids": [item.id for item in conflicts],
                },
            )

            response = serialize_window(reservation, conflicts, now)
            db.session.commit()
            return response
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def delete_window(reservation_id, actor_user_id):
        try:
            reservation = db.session.get(Reservation, reservation_id)
            if reservation is None or reservation.status != MAINTENANCE_STATUS:
                abort(404, message="A karbantartási idősáv nem található.")

            create_audit_log(
                action="MAINTENANCE_DELETED",
                entity_name="reservations",
                entity_value=reservation.id,
                user_id=actor_user_id,
                old_value={
                    "status": reservation.status,
                    "room_id": reservation.room_id,
                    "start_time": reservation.start_time,
                    "end_time": reservation.end_time,
                },
            )
            db.session.delete(reservation)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def update_conflicting_reservation(reservation_id, data, actor_user_id):
        """
        Aktív/függő foglalás áthelyezése;
        karbantartással vagy más foglalással nem ütközhet.
        """
        try:
            reservation = (
                Reservation.query.options(joinedload(Reservation.users))
                .filter(Reservation.id == reservation_id)
                .first()
            )
            if (
                reservation is None
                or reservation.status not in BLOCKING_RESERVATION_STATUSES
            ):
                abort(404, message="A módosítható foglalás nem található.")

            room_id = data["room_id"].strip()
            start_time = data["start_time"]
            end_time = data["end_time"]
            now = datetime.now()

            if start_time.tzinfo is not None or end_time.tzinfo is not None:
                abort(400, message="Az időpontokat időzóna nélkül kell megadni.")
            if end_time <= start_time:
                abort(400, message="A foglalás végének a kezdete után kell lennie.")
            if start_time < now:
                abort(400, message="A foglalás új kezdete nem lehet a múltban.")
            if db.session.get(Classroom, room_id) is None:
                abort(404, message="A megadott terem nem található.")

            maintenance = MaintenanceService.find_overlapping_window(
                room_id, start_time, end_time
            )
            if maintenance is not None:
                abort(
                    409,
                    message=(
                        f"A foglalás nem helyezhető át: a(z) {room_id} terem "
                        "karbantartás alatt áll "
                        f"({MaintenanceService.describe_window(maintenance)})."
                    ),
                )

            overlap = (
                Reservation.query.filter(
                    Reservation.id != reservation.id,
                    Reservation.room_id == room_id,
                    Reservation.status.in_(BLOCKING_RESERVATION_STATUSES),
                    Reservation.start_time < end_time,
                    Reservation.end_time > start_time,
                )
                .order_by(Reservation.start_time)
                .first()
            )
            if overlap is not None:
                abort(
                    409,
                    message=(
                        f"A kiválasztott időpont másik foglalással ütközik "
                        f"(#{overlap.id}, "
                        f"{MaintenanceService.describe_window(overlap)})."
                    ),
                )

            old_value = {
                "room_id": reservation.room_id,
                "start_time": reservation.start_time,
                "end_time": reservation.end_time,
                "status": reservation.status,
            }
            reservation.room_id = room_id
            reservation.start_time = start_time
            reservation.end_time = end_time

            create_audit_log(
                action="RESERVATION_RESCHEDULED_FOR_MAINTENANCE",
                entity_name="reservations",
                entity_value=reservation.id,
                user_id=actor_user_id,
                old_value=old_value,
                new_value={
                    "room_id": reservation.room_id,
                    "start_time": reservation.start_time,
                    "end_time": reservation.end_time,
                    "status": reservation.status,
                },
            )
            db.session.commit()
            return serialize_conflict(reservation)
        except Exception:
            db.session.rollback()
            raise
