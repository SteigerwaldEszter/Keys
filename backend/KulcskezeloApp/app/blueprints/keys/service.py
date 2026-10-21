import time

from apiflask import abort
from sqlalchemy.exc import IntegrityError

from app.blueprints.reports.service import create_audit_log
from app.extensions import db
from app.models.key import Key
from app.models.key_log import KeyLog
from app.models.reservation import Reservation
from app.models.signature import Signature


def get_key_data(key):
    return {
        "room_id": key.room_id,
        "name": key.name,
        "status": key.status,
        "is_master": key.is_master,
    }


def get_all_keys():
    return Key.query.all()


def create_or_update_key(
    key_data,
    key_id=None,
    actor_user_id=None,
):
    try:
        if key_id is not None:
            key = Key.query.filter_by(id=key_id).with_for_update().first_or_404()

            old_data = get_key_data(key)

            key.room_id = key_data.get("room_id", key.room_id)
            key.name = key_data.get("name", key.name)
            key.is_master = key_data.get("is_master", key.is_master)

            if "status" in key_data:
                key.status = key_data["status"]

            audit_action = "KEY_UPDATED"

        else:
            key = Key(
                room_id=key_data["room_id"],
                name=key_data["name"],
                is_master=key_data.get("is_master", False),
                status=key_data.get("status", "available"),
            )

            db.session.add(key)

            old_data = None
            audit_action = "KEY_CREATED"

        db.session.flush()

        new_data = get_key_data(key)

        if old_data is None or old_data != new_data:
            create_audit_log(
                action=audit_action,
                entity_name="keys",
                entity_value=key.id,
                user_id=actor_user_id,
                old_value=old_data,
                new_value=new_data,
            )

        db.session.commit()
        return key

    except Exception:
        db.session.rollback()
        raise


def handover_key_action(
    key_id: int,
    reservation_id: int,
    receiver_id: int,
    auth_format: str,
    signature_payload: str,
    handler_user_id: int,
):
    try:
        key = Key.query.filter_by(id=key_id).with_for_update().first_or_404()

        if key.status != "available":
            abort(
                400,
                message="Ez a kulcs jelenleg nem adható ki!",
            )

        reservation = Reservation.query.get_or_404(reservation_id)

        if not key.is_master:
            if key.room_id != reservation.room_id:
                abort(
                    400,
                    message="A kulcs nem ehhez a teremhez tartozik!",
                )

        old_status = key.status

        signature = Signature(
            format=auth_format,
            payload=signature_payload,
        )

        db.session.add(signature)
        db.session.flush()

        key_log = KeyLog(
            key_id=key.id,
            reservation_id=reservation_id,
            handler_id=handler_user_id,
            receiver_id=receiver_id,
            signature_id=signature.id,
            action="ISSUE",
        )

        db.session.add(key_log)
        db.session.flush()

        key.status = "handed_out"

        audit_action = "MASTER_KEY_CHECKOUT" if key.is_master else "KEY_CHECKOUT"

        create_audit_log(
            action=audit_action,
            entity_name="keys",
            entity_value=key.id,
            user_id=handler_user_id,
            old_value={
                "status": old_status,
            },
            new_value={
                "status": key.status,
                "room_id": key.room_id,
                "reservation_id": reservation_id,
                "receiver_id": receiver_id,
                "handler_id": handler_user_id,
                "key_log_id": key_log.id,
                "auth_format": auth_format,
                "is_master": key.is_master,
            },
        )

        db.session.commit()

        return {
            "message": "Kulcs sikeresen kiadva",
            "key_id": key.id,
        }

    except Exception:
        db.session.rollback()
        raise


def return_key_action(
    key_id: int,
    reservation_id: int,
    receiver_id: int,
    auth_format: str,
    signature_payload: str,
    handler_user_id: int,
):
    try:
        key = Key.query.filter_by(id=key_id).with_for_update().first_or_404()

        if key.status != "handed_out":
            abort(
                400,
                message="Ez a kulcs nincs kiadva!",
            )

        last_log = (
            KeyLog.query.filter_by(key_id=key.id).order_by(KeyLog.id.desc()).first()
        )

        if (
            last_log is None
            or last_log.action != "ISSUE"
            or last_log.reservation_id != reservation_id
        ):
            abort(
                400,
                message="A kulcskiadás adatai nem egyeznek!",
            )

        old_status = key.status

        signature = Signature(
            format=auth_format,
            payload=signature_payload,
        )

        db.session.add(signature)
        db.session.flush()

        key_log = KeyLog(
            key_id=key.id,
            reservation_id=reservation_id,
            handler_id=handler_user_id,
            receiver_id=receiver_id,
            signature_id=signature.id,
            action="RETURN",
        )

        db.session.add(key_log)
        db.session.flush()

        key.status = "available"

        audit_action = "MASTER_KEY_RETURN" if key.is_master else "KEY_RETURN"

        create_audit_log(
            action=audit_action,
            entity_name="keys",
            entity_value=key.id,
            user_id=handler_user_id,
            old_value={
                "status": old_status,
            },
            new_value={
                "status": key.status,
                "room_id": key.room_id,
                "reservation_id": reservation_id,
                "receiver_id": receiver_id,
                "handler_id": handler_user_id,
                "key_log_id": key_log.id,
                "auth_format": auth_format,
                "is_master": key.is_master,
            },
        )

        db.session.commit()

        return {
            "message": "Kulcs sikeresen visszavéve",
            "key_id": key.id,
        }

    except Exception:
        db.session.rollback()
        raise


def delete_key_action(
    key_id: int,
    actor_user_id=None,
):
    try:
        key = Key.query.get_or_404(key_id)

        old_data = get_key_data(key)

        create_audit_log(
            action="KEY_DELETED",
            entity_name="keys",
            entity_value=key.id,
            user_id=actor_user_id,
            old_value=old_data,
        )

        db.session.delete(key)
        db.session.commit()

        return {
            "message": "Kulcs sikeresen törölve.",
            "key_id": key_id,
        }

    except IntegrityError:
        db.session.rollback()

        abort(
            409,
            message=("A kulcs nem törölhető, mert kapcsolódó naplóbejegyzése van."),
        )

    except Exception:
        db.session.rollback()
        raise


temp_signatures_cache = {}


def save_temp_signature_action(
    token,
    format_str,
    payload_str,
):
    temp_signatures_cache[token] = {
        "format": format_str,
        "payload": payload_str,
        "timestamp": time.time(),
    }

    now = time.time()

    keys_to_delete = [
        k for k, v in temp_signatures_cache.items() if now - v["timestamp"] > 600
    ]

    for k in keys_to_delete:
        del temp_signatures_cache[k]


def check_temp_signature_action(token):
    if token in temp_signatures_cache:
        data = temp_signatures_cache.pop(token)

        return {
            "status": "ready",
            "format": data["format"],
            "payload": data["payload"],
        }

    return {"status": "waiting"}
