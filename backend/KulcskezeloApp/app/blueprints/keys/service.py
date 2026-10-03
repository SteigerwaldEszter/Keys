from app.extensions import db
from app.models.key import Key
from app.models.key_log import KeyLog
from app.models.reservation import Reservation
from app.models.signature import Signature


def get_all_keys():
    # Összes kulcs lekérése státusszal és mesterkulcs jelöléssel
    return Key.query.all()


def create_or_update_key(key_data, key_id=None):
    # Kulcstörzs és mesterkulcs mentése (Admin)
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


def issue_key_action(
    key_id: int,
    reservation_id: int,
    receiver_id: int,
    auth_format: str,
    signature_payload: str,
    handler_user_id: int,
):
    key = Key.query.get_or_404(key_id)
    Reservation.query.get_or_404(reservation_id)

    # 1. Aláírás / jóváhagyás rögzítése
    signature = Signature(format=auth_format, payload=signature_payload)
    db.session.add(signature)
    db.session.flush()

    # 2. Naplóbejegyzés létrehozása
    log = KeyLog(
        key_id=key.id,
        reservation_id=reservation_id,
        handler_id=handler_user_id,
        receiver_id=receiver_id,
        signature_id=signature.id,
        action="ISSUE",
    )
    db.session.add(log)

    # 3. Kulcs státusz frissítése
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

    # 1. Visszavételi szignó mentése
    signature = Signature(format=auth_format, payload=signature_payload)
    db.session.add(signature)
    db.session.flush()

    # 2. Naplóbejegyzés létrehozása
    log = KeyLog(
        key_id=key.id,
        reservation_id=reservation_id,
        handler_id=handler_user_id,
        receiver_id=receiver_id,
        signature_id=signature.id,
        action="RETURN",
    )
    db.session.add(log)

    # 3. Kulcs státusz szabaddá tétele
    key.status = "available"

    db.session.commit()
    return {"message": "Kulcs sikeresen visszavéve", "key_id": key.id}
