from datetime import timedelta

from app.blueprints.reports.service import create_audit_log
from app.extensions import db
from app.models.reservation import Reservation


class ReservationService:
    @staticmethod
    def get_reservations(current_user):
        try:
            roles = (
                current_user.get("roles", []) if isinstance(current_user, dict) else []
            )

            if any(role in roles for role in ["Admin", "Director", "Receptionist"]):
                reservations = Reservation.query.all()
            else:
                user_id = current_user.get("user_id")

                reservations = Reservation.query.filter_by(user_id=user_id).all()

            return True, {"reservations": reservations}

        except Exception:
            return False, "Hiba történt a foglalások lekérdezésekor."

    @staticmethod
    def create_reservation(current_user, data):
        try:
            base_start_time = data["start_time"]
            room_id = data["room_id"]
            duration_slots = data.get("duration_slots", 1)
            recurring_weeks = data.get("recurring_weeks", 1)
            user_id = current_user.get("user_id")

            if duration_slots < 1 or duration_slots > 6:
                return False, "A blokkok száma 1 és 6 között lehet."

            if recurring_weeks < 1 or recurring_weeks > 15:
                return False, ("Az ismétlődések száma 1 és 15 hét között lehet.")

            reservations_to_create = []

            for week in range(recurring_weeks):
                current_start = base_start_time + timedelta(weeks=week)

                current_end = current_start + timedelta(minutes=45 * duration_slots)

                conflicting_reservation = Reservation.query.filter(
                    Reservation.room_id == room_id,
                    Reservation.status.in_(["pending", "active"]),
                    Reservation.start_time < current_end,
                    Reservation.end_time > current_start,
                ).first()

                if conflicting_reservation:
                    return False, (
                        f"A foglalás sikertelen: Ütközés történt "
                        f"a(z) {week + 1}. héten "
                        f"({current_start.strftime('%Y-%m-%d %H:%M')}). "
                        f"Kérjük, válasszon másik időpontot "
                        f"vagy termet."
                    )

                new_reservation = Reservation(
                    user_id=user_id,
                    room_id=room_id,
                    start_time=current_start,
                    end_time=current_end,
                    status="active",
                )

                reservations_to_create.append(new_reservation)

            db.session.add_all(reservations_to_create)

            db.session.flush()

            for reservation in reservations_to_create:
                create_audit_log(
                    action="BOOKING_CREATED",
                    entity_name="reservations",
                    entity_value=reservation.id,
                    user_id=user_id,
                    new_value={
                        "user_id": reservation.user_id,
                        "room_id": reservation.room_id,
                        "start_time": reservation.start_time,
                        "end_time": reservation.end_time,
                        "status": reservation.status,
                    },
                )

            db.session.commit()

            return True, {
                "message": (
                    f"Sikeresen létrejött {len(reservations_to_create)} db foglalás."
                )
            }

        except Exception as e:
            db.session.rollback()

            return False, (f"Hiba a foglalás(ok) létrehozásakor: {e!s}")

    @staticmethod
    def update_status(reservation_id, new_status, current_user):
        try:
            reservation = Reservation.query.get(reservation_id)

            if not reservation:
                return False, "A keresett foglalás nem található."

            allowed_statuses = [
                "cancelled",
                "no-show",
                "active",
                "pending",
                "completed",
            ]

            if new_status not in allowed_statuses:
                return False, "Érvénytelen státusz."

            old_status = reservation.status

            if old_status == new_status:
                return True, reservation

            reservation.status = new_status

            user_id = (
                current_user.get("user_id") if isinstance(current_user, dict) else None
            )

            if new_status == "cancelled":
                action = "BOOKING_CANCELLED"

            elif new_status == "no-show":
                action = "BOOKING_NO_SHOW"

            else:
                action = "BOOKING_UPDATED"

            create_audit_log(
                action=action,
                entity_name="reservations",
                entity_value=reservation.id,
                user_id=user_id,
                old_value={
                    "status": old_status,
                },
                new_value={
                    "status": new_status,
                },
            )

            db.session.commit()

            return True, reservation

        except Exception:
            db.session.rollback()

            return False, "Hiba a státusz frissítésekor."

    @staticmethod
    def delete_reservation(reservation_id, current_user):
        try:
            reservation = Reservation.query.get(reservation_id)

            if not reservation:
                return False, "A keresett foglalás nem található."

            roles = (
                current_user.get("roles", []) if isinstance(current_user, dict) else []
            )

            user_id = current_user.get("user_id")

            if "Admin" not in roles:
                if reservation.user_id != user_id:
                    return False, ("Nincs jogosultsága a foglalás törléséhez.")

            old_data = {
                "user_id": reservation.user_id,
                "room_id": reservation.room_id,
                "start_time": reservation.start_time,
                "end_time": reservation.end_time,
                "status": reservation.status,
            }

            create_audit_log(
                action="BOOKING_DELETED",
                entity_name="reservations",
                entity_value=reservation.id,
                user_id=user_id,
                old_value=old_data,
            )

            db.session.delete(reservation)

            db.session.commit()

            return True, None

        except Exception as e:
            db.session.rollback()

            return False, (f"Hiba a foglalás törlésekor: {e!s}")
