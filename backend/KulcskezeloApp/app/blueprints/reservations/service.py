from datetime import timedelta

from app.extensions import db
from app.models.reservation import Reservation


class ReservationService:
    @staticmethod
    def get_reservations(current_user):
        try:
            user_roles = []

            roles = (
                current_user.get("roles", []) if isinstance(current_user, dict) else []
            )

            for role in roles:
                user_roles.append(role)

            if any(
                role in user_roles for role in ["Admin", "Director", "Receptionist"]
            ):
                reservations = Reservation.query.all()
            else:
                user_id = user_id = current_user.get("user_id")
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
            user_id = user_id = current_user.get("user_id")

            if duration_slots < 1 or duration_slots > 6:
                return False, "A blokkok száma 1 és 6 között lehet."
            if recurring_weeks < 1 or recurring_weeks > 15:
                return False, "Az ismétlődések száma 1 és 15 hét között lehet."

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
                        f"A foglalás sikertelen: Ütközés történt a(z) {week + 1}. "
                        f"héten ({current_start.strftime('%Y-%m-%d %H:%M')}). "
                        f"Kérjük, válasszon másik időpontot vagy termet."
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
            db.session.commit()

            return True, {
                "message": f"Sikeresen létrejött {len(reservations_to_create)} "
                f"db foglalás."
            }

        except Exception as e:
            db.session.rollback()
            return False, f"Hiba a foglalás(ok) létrehozásakor: {e!s}"

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

            reservation.status = new_status
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
            user_roles = []
            roles = (
                current_user.get("roles", []) if isinstance(current_user, dict) else []
            )
            for role in roles:
                user_roles.append(role)
            if "Admin" not in user_roles:
                if reservation.user_id != current_user.get("user_id"):
                    return False, "Nincs jogosultsága a foglalás törléséhez."
            db.session.delete(reservation)
            db.session.commit()
            return True, None
        except Exception as e:
            db.session.rollback()
            return False, f"Hiba a foglalás törlésekor: {e!s}"
