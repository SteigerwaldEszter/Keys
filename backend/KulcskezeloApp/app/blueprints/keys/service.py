import time

from apiflask import abort

from app.extensions import db
from app.models.key import Key
from app.models.key_log import KeyLog
from app.models.reservation import Reservation
from app.models.signature import Signature


def get_all_keys():
    return Key.query.all()


def create_or_update_key(key_data, key_id=None):
    if key_id:
        key = Key.query.get_or_404(key_id)
        key.room_id = key_data.get("room_id", key.room_id)
        key.name = key_data.get("name", key.name)
        key.is_master = key_data.get("is_master", key.is_master)
        if "status" in key_data:
            key.status = key_data["status"]
    else:
        key = Key(
            room_id=key_data["room_id"],
            name=key_data["name"],
            is_master=key_data.get("is_master", False),
            status=key_data.get("status", "available"),
        )
        db.session.add(key)

    db.session.commit()
    return key


def handover_key_action(
    key_id: int,
    reservation_id: int,
    receiver_id: int,
    auth_format: str,
    signature_payload: str,
    handler_user_id: int,
):
    key = Key.query.get_or_404(key_id)

    if key.status == "handed_out":
        abort(400, "Ez a kulcs már ki van adva!")

    Reservation.query.get_or_404(reservation_id)

    signature = Signature(format=auth_format, payload=signature_payload)
    db.session.add(signature)
    db.session.flush()

    log = KeyLog(
        key_id=key.id,
        reservation_id=reservation_id,
        handler_id=handler_user_id,
        receiver_id=receiver_id,
        signature_id=signature.id,
        action="ISSUE",
    )
    db.session.add(log)

    key.status = "handed_out"

    db.session.commit()
    return {"message": "Kulcs sikeresen kiadva", "key_id": key.id}


def return_key_action(
    key_id: int,
    reservation_id: int,
    receiver_id: int,
    auth_format: str,
    signature_payload: str,
    handler_user_id: int,
):
    key = Key.query.get_or_404(key_id)

    signature = Signature(format=auth_format, payload=signature_payload)
    db.session.add(signature)
    db.session.flush()

    log = KeyLog(
        key_id=key.id,
        reservation_id=reservation_id,
        handler_id=handler_user_id,
        receiver_id=receiver_id,
        signature_id=signature.id,
        action="RETURN",
    )
    db.session.add(log)

    key.status = "available"

    db.session.commit()
    return {"message": "Kulcs sikeresen visszavéve", "key_id": key.id}


def delete_key_action(key_id: int):
    key = Key.query.get(key_id)

    if not key:
        abort(404, message="A megadott kulcs nem található.")

    try:
        db.session.delete(key)
        db.session.commit()
        return {"message": "Kulcs sikeresen törölve.", "key_id": key_id}
    except Exception:
        db.session.rollback()
        abort(
            400,
            message="Ezt a kulcsot nem lehet törölni, "
            "mert már szerepel egy foglalásban vagy eseménynaplóban.",
        )


temp_signatures_cache = {}


def save_temp_signature_action(token, format_str, payload_str):

    temp_signatures_cache[token] = {
        "format": format_str,
        "payload": payload_str,
        "timestamp": time.time(),
    }

    # Régitokenek takarítása a memóriából
    keys_to_delete = [
        k
        for k, v in temp_signatures_cache.items()
        if time.time() - v["timestamp"] > 600
    ]
    for k in keys_to_delete:
        del temp_signatures_cache[k]


def check_temp_signature_action(token):

    if token in temp_signatures_cache:
        data = temp_signatures_cache.pop(token)

        return {"status": "ready", "format": data["format"], "payload": data["payload"]}

    return {"status": "waiting"}
