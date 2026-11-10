from apiflask import APIBlueprint, HTTPError

from app.blueprints import role_required
from app.extensions import auth

from .master_key_schemas import (
    MasterKeyDetailsSchema,
    MasterKeyMessageSchema,
    MasterKeyRoomRequestSchema,
    MasterKeysListSchema,
    MasterKeyUserRequestSchema,
)
from .master_keys import (
    assign_master_key_room,
    get_master_key_details,
    grant_master_key_user,
    list_master_keys,
    remove_master_key_room,
    revoke_master_key_user,
    validate_master_key_handover,
)
from .schemas import (
    KeyCreateUpdateSchema,
    KeyHandoverSchema,
    KeyOutSchema,
    KeyReturnSchema,
    MessageOut,
    OverdueKeyOut,
    TempSignatureIn,
    TempSignatureOut,
)
from .service import (
    check_temp_signature_action,
    create_or_update_key,
    delete_key_action,
    get_all_keys,
    get_overdue_keys_action,
    handover_key_action,
    return_key_action,
    save_temp_signature_action,
)

bp = APIBlueprint("keys", __name__, url_prefix="/api/keys")


@bp.get("")
@bp.output(KeyOutSchema(many=True))
@bp.auth_required(auth)
def list_keys():
    return get_all_keys()


@bp.get("/overdue")
@bp.output(OverdueKeyOut(many=True))
@bp.auth_required(auth)
@role_required(["Receptionist", "Admin"])
def overdue_keys():
    success, result = get_overdue_keys_action()

    if success:
        return result

    raise HTTPError(400, result)


@bp.post("/")
@bp.input(KeyCreateUpdateSchema)
@bp.output(KeyOutSchema, status_code=201)
@bp.auth_required(auth)
@role_required("Admin")
def create_key(json_data):
    success, result = create_or_update_key(
        json_data,
        actor_user_id=auth.current_user["user_id"],
    )

    if success:
        return result

    raise HTTPError(400, result)


@bp.put("/<int:key_id>")
@bp.input(KeyCreateUpdateSchema)
@bp.output(KeyOutSchema)
@bp.auth_required(auth)
@role_required("Admin")
def update_key(key_id, json_data):
    success, result = create_or_update_key(
        json_data,
        key_id=key_id,
        actor_user_id=auth.current_user["user_id"],
    )

    if success:
        return result

    raise HTTPError(400, result)


@bp.post("/<int:key_id>/handover")
@bp.auth_required(auth)
@role_required("Receptionist")
@bp.input(KeyHandoverSchema)
def handover_key(key_id, json_data):
    validate_master_key_handover(
        key_id=key_id,
        reservation_id=json_data["reservation_id"],
        receiver_id=json_data["receiver_id"],
        handler_user_id=auth.current_user["user_id"],
    )

    success, result = handover_key_action(
        key_id=key_id,
        reservation_id=json_data["reservation_id"],
        receiver_id=json_data["receiver_id"],
        auth_format=json_data["format"],
        signature_payload=json_data["payload"],
        handler_user_id=auth.current_user["user_id"],
        pin=json_data["pin"],
    )

    if success:
        return result

    raise HTTPError(400, result)


@bp.post("/<int:key_id>/return")
@bp.input(KeyReturnSchema)
@bp.auth_required(auth)
@role_required("Receptionist")
def return_key(key_id, json_data):
    success, result = return_key_action(
        key_id=key_id,
        reservation_id=json_data["reservation_id"],
        receiver_id=json_data["receiver_id"],
        auth_format=json_data["format"],
        signature_payload=json_data["payload"],
        handler_user_id=auth.current_user["user_id"],
    )

    if success:
        return result

    raise HTTPError(400, result)


@bp.delete("/<int:key_id>")
@bp.auth_required(auth)
@role_required("Admin")
def delete_key(key_id):
    success, result = delete_key_action(
        key_id,
        actor_user_id=auth.current_user["user_id"],
    )

    if success:
        return "", 204

    raise HTTPError(400, result)


@bp.get("/master-permissions")
@bp.auth_required(auth)
@role_required(["Admin", "Receptionist", "Director"])
@bp.output(MasterKeysListSchema)
def get_master_keys():
    return list_master_keys()


@bp.get("/<int:key_id>/master-permissions")
@bp.auth_required(auth)
@role_required(["Admin", "Receptionist", "Director"])
@bp.output(MasterKeyDetailsSchema)
def get_key_master_permissions(key_id):
    return get_master_key_details(key_id)


@bp.post("/<int:key_id>/master-permissions/users")
@bp.auth_required(auth)
@role_required("Admin")
@bp.input(MasterKeyUserRequestSchema)
@bp.output(MasterKeyMessageSchema, status_code=201)
def grant_key_master_user(key_id, json_data):
    return grant_master_key_user(
        key_id,
        json_data["user_id"],
        auth.current_user["user_id"],
    )


@bp.delete("/<int:key_id>/master-permissions/users/<int:user_id>")
@bp.auth_required(auth)
@role_required("Admin")
@bp.output(MasterKeyMessageSchema)
def revoke_key_master_user(key_id, user_id):
    return revoke_master_key_user(
        key_id,
        user_id,
        auth.current_user["user_id"],
    )


@bp.post("/<int:key_id>/master-permissions/rooms")
@bp.auth_required(auth)
@role_required("Admin")
@bp.input(MasterKeyRoomRequestSchema)
@bp.output(MasterKeyMessageSchema, status_code=201)
def assign_key_master_room(key_id, json_data):
    return assign_master_key_room(
        key_id,
        json_data["room_id"],
        auth.current_user["user_id"],
    )


@bp.delete("/<int:key_id>/master-permissions/rooms/<string:room_id>")
@bp.auth_required(auth)
@role_required("Admin")
@bp.output(MasterKeyMessageSchema)
def remove_key_master_room(key_id, room_id):
    return remove_master_key_room(
        key_id,
        room_id,
        auth.current_user["user_id"],
    )


@bp.post("/api/signature/<string:token>")
@bp.input(TempSignatureIn)
@bp.output(MessageOut, status_code=200)
def save_temp_signature(token, json_data):
    success, result = save_temp_signature_action(
        token=token,
        format_str=json_data["format"],
        payload_str=json_data["payload"],
    )

    if success:
        return result

    raise HTTPError(400, result)


@bp.get("/api/signature/<string:token>")
@bp.output(TempSignatureOut, status_code=200)
def check_temp_signature(token):
    success, result = check_temp_signature_action(token)

    if success:
        return result

    raise HTTPError(400, result)
