from apiflask import abort
from flask import current_app

from app.blueprints.reports.service import create_audit_log
from app.extensions import db
from app.models.classroom import Classroom
from app.models.key import Key
from app.models.master_key_permissions import MasterKeyPermissions
from app.models.master_key_rooms import MasterKeyRooms
from app.models.reservation import Reservation
from app.models.user import User


def _get_master_key(key_id, lock=False):
    query = Key.query.filter_by(id=key_id)

    if lock:
        query = query.with_for_update()

    key = query.first()

    if key is None:
        abort(404, message="A kulcs nem található.")

    if not key.is_master:
        abort(400, message="A megadott kulcs nem mesterkulcs.")

    return key


def list_master_keys():
    keys = Key.query.filter_by(is_master=True).order_by(Key.id).all()

    return {
        "master_keys": [
            {
                "id": key.id,
                "name": key.name,
                "status": key.status,
                "is_master": True,
            }
            for key in keys
        ]
    }


def get_master_key_details(key_id):
    key = _get_master_key(key_id)

    users = []

    for permission in MasterKeyPermissions.query.filter_by(key_id=key_id).all():
        user = db.session.get(User, permission.user_id)

        if user is not None:
            users.append(
                {
                    "id": user.id,
                    "name": user.name,
                }
            )

    rooms = []

    for assignment in MasterKeyRooms.query.filter_by(key_id=key_id).all():
        room = db.session.get(Classroom, assignment.room_id)

        if room is not None:
            rooms.append(
                {
                    "id": room.id,
                    "capacity": room.capacity,
                }
            )

    return {
        "key_id": key.id,
        "name": key.name,
        "status": key.status,
        "users": sorted(users, key=lambda item: item["id"]),
        "rooms": sorted(rooms, key=lambda item: item["id"]),
    }


def grant_master_key_user(key_id, user_id, actor_user_id):
    try:
        _get_master_key(key_id, lock=True)

        user = db.session.get(User, user_id)

        if user is None:
            abort(404, message="A felhasználó nem található.")

        if not user.is_active:
            abort(
                400,
                message="Inaktív felhasználó nem kaphat jogosultságot.",
            )

        existing = db.session.get(
            MasterKeyPermissions,
            (key_id, user_id),
        )

        if existing is not None:
            abort(
                409,
                message="A felhasználónak már van jogosultsága.",
            )

        db.session.add(
            MasterKeyPermissions(
                key_id=key_id,
                user_id=user_id,
            )
        )

        create_audit_log(
            action="MASTER_KEY_USER_GRANTED",
            entity_name="master_key_permissions",
            entity_value=f"{key_id}:{user_id}",
            user_id=actor_user_id,
            new_value={
                "key_id": key_id,
                "user_id": user_id,
            },
        )

        db.session.commit()

        return {"message": "Mesterkulcs-jogosultság hozzáadva."}

    except Exception:
        db.session.rollback()
        raise


def revoke_master_key_user(key_id, user_id, actor_user_id):
    try:
        _get_master_key(key_id, lock=True)

        permission = db.session.get(
            MasterKeyPermissions,
            (key_id, user_id),
        )

        if permission is None:
            abort(404, message="A jogosultság nem található.")

        create_audit_log(
            action="MASTER_KEY_USER_REVOKED",
            entity_name="master_key_permissions",
            entity_value=f"{key_id}:{user_id}",
            user_id=actor_user_id,
            old_value={
                "key_id": key_id,
                "user_id": user_id,
            },
        )

        db.session.delete(permission)
        db.session.commit()

        return {"message": "Mesterkulcs-jogosultság visszavonva."}

    except Exception:
        db.session.rollback()
        raise


def assign_master_key_room(key_id, room_id, actor_user_id):
    try:
        _get_master_key(key_id, lock=True)

        room = db.session.get(Classroom, room_id)

        if room is None:
            abort(404, message="A terem nem található.")

        if not room.is_active:
            abort(
                400,
                message="Inaktív terem nem rendelhető mesterkulcshoz.",
            )

        existing = db.session.get(
            MasterKeyRooms,
            (key_id, room_id),
        )

        if existing is not None:
            abort(
                409,
                message="A terem már hozzá van rendelve.",
            )

        db.session.add(
            MasterKeyRooms(
                key_id=key_id,
                room_id=room_id,
            )
        )

        create_audit_log(
            action="MASTER_KEY_ROOM_ASSIGNED",
            entity_name="master_key_rooms",
            entity_value=f"{key_id}:{room_id}",
            user_id=actor_user_id,
            new_value={
                "key_id": key_id,
                "room_id": room_id,
            },
        )

        db.session.commit()

        return {"message": "Terem hozzárendelve a mesterkulcshoz."}

    except Exception:
        db.session.rollback()
        raise


def remove_master_key_room(key_id, room_id, actor_user_id):
    try:
        _get_master_key(key_id, lock=True)

        assignment = db.session.get(
            MasterKeyRooms,
            (key_id, room_id),
        )

        if assignment is None:
            abort(
                404,
                message="A terem-hozzárendelés nem található.",
            )

        create_audit_log(
            action="MASTER_KEY_ROOM_REMOVED",
            entity_name="master_key_rooms",
            entity_value=f"{key_id}:{room_id}",
            user_id=actor_user_id,
            old_value={
                "key_id": key_id,
                "room_id": room_id,
            },
        )

        db.session.delete(assignment)
        db.session.commit()

        return {"message": "Terem-hozzárendelés törölve."}

    except Exception:
        db.session.rollback()
        raise


def validate_master_key_handover(
    key_id,
    reservation_id,
    receiver_id,
    handler_user_id,
):
    key = Key.query.filter_by(id=key_id).with_for_update().first_or_404()

    if not key.is_master:
        return

    reservation = db.session.get(Reservation, reservation_id)

    if reservation is None:
        abort(404, message="A foglalás nem található.")

    receiver = db.session.get(User, receiver_id)

    if receiver is None or not receiver.is_active:
        _deny_master_key(
            key_id,
            reservation_id,
            receiver_id,
            handler_user_id,
            "inactive_receiver",
        )

    if reservation.user_id != receiver_id:
        _deny_master_key(
            key_id,
            reservation_id,
            receiver_id,
            handler_user_id,
            "wrong_receiver",
        )

    permission = db.session.get(
        MasterKeyPermissions,
        (key_id, receiver_id),
    )

    if permission is None:
        _deny_master_key(
            key_id,
            reservation_id,
            receiver_id,
            handler_user_id,
            "user_not_authorized",
        )

    assigned_room = db.session.get(
        MasterKeyRooms,
        (key_id, reservation.room_id),
    )

    if assigned_room is None:
        _deny_master_key(
            key_id,
            reservation_id,
            receiver_id,
            handler_user_id,
            "room_not_covered",
        )


def _deny_master_key(
    key_id,
    reservation_id,
    receiver_id,
    handler_user_id,
    reason,
):
    try:
        create_audit_log(
            action="MASTER_KEY_ACCESS_DENIED",
            entity_name="keys",
            entity_value=key_id,
            user_id=handler_user_id,
            new_value={
                "reservation_id": reservation_id,
                "receiver_id": receiver_id,
                "reason": reason,
            },
        )

        db.session.commit()

    except Exception:
        db.session.rollback()
        current_app.logger.exception("Nem sikerült naplózni a mesterkulcs-elutasítást.")

    abort(
        403,
        message=("A mesterkulcs átvétele nem engedélyezett ehhez a foglaláshoz."),
    )
