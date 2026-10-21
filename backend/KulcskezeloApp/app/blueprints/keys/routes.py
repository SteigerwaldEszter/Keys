from apiflask import APIBlueprint

from app.blueprints import role_required
from app.extensions import auth

from .schemas import (
    KeyCreateUpdateSchema,
    KeyHandoverSchema,
    KeyOutSchema,
    KeyReturnSchema,
)
from .service import (
    create_or_update_key,
    delete_key_action,
    get_all_keys,
    handover_key_action,
    return_key_action,
)

bp = APIBlueprint("keys", __name__, url_prefix="/api/keys")


@bp.get("")
@bp.output(KeyOutSchema(many=True))
@bp.auth_required(auth)
def list_keys():
    return get_all_keys()


@bp.post("/")
@bp.input(KeyCreateUpdateSchema)
@bp.output(KeyOutSchema, status_code=201)
@bp.auth_required(auth)
@role_required("Admin")
def create_key(json_data):
    return create_or_update_key(json_data)


@bp.put("/<int:key_id>")
@bp.input(KeyCreateUpdateSchema)
@bp.output(KeyOutSchema)
@bp.auth_required(auth)
@role_required("Admin")
def update_key(key_id, json_data):
    return create_or_update_key(json_data, key_id=key_id)


@bp.post("/<int:key_id>/handover")
@bp.auth_required(auth)
@role_required("Receptionist")
@bp.input(KeyHandoverSchema)
def handover_key(key_id, json_data):
    return handover_key_action(
        key_id=key_id,
        reservation_id=json_data["reservation_id"],
        receiver_id=json_data["receiver_id"],
        auth_format=json_data["format"],
        signature_payload=json_data["payload"],
        handler_user_id=auth.current_user["user_id"],
    ), 200


@bp.post("/<int:key_id>/return")
@bp.input(KeyReturnSchema)
@bp.auth_required(auth)
@role_required("Receptionist")
def return_key(key_id, json_data):
    return (
        return_key_action(
            key_id=key_id,
            reservation_id=json_data["reservation_id"],
            receiver_id=json_data["receiver_id"],
            auth_format=json_data["format"],
            signature_payload=json_data["payload"],
            handler_user_id=1,
        ),
        200,
    )


@bp.delete("/<int:key_id>")
@bp.auth_required(auth)
@role_required("Admin")
def delete_key(key_id):
    return delete_key_action(key_id)
