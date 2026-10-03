from apiflask import APIBlueprint

from .schemas import (
    KeyCreateUpdateSchema,
    KeyIssueSchema,
    KeyOutSchema,
    KeyReturnSchema,
)
from .service import (
    create_or_update_key,
    get_all_keys,
    issue_key_action,
    return_key_action,
)

bp = APIBlueprint("keys", __name__, url_prefix="/api/keys")


@bp.get("")
@bp.output(KeyOutSchema(many=True))
def list_keys():
    """Kulcsok listázása állapottal és mesterkulcs jelöléssel"""
    return get_all_keys()


@bp.post("")
@bp.input(KeyCreateUpdateSchema)
@bp.output(KeyOutSchema, status_code=201)
def create_key(data):
    """Kulcstörzs és mesterkulcs rögzítése (Adminisztrátor)"""
    return create_or_update_key(data)


@bp.put("/<int:key_id>")
@bp.input(KeyCreateUpdateSchema)
@bp.output(KeyOutSchema)
def update_key(key_id, data):
    """Kulcs módosítása (Adminisztrátor)"""
    return create_or_update_key(data, key_id=key_id)


@bp.post("/<int:key_id>/issue")
@bp.input(KeyIssueSchema)
def issue_key(key_id, data):
    """Kulcs kiadásának rögzítése (Portás/Operátor)"""
    return (
        issue_key_action(
            key_id=key_id,
            reservation_id=data["reservation_id"],
            receiver_id=data["receiver_id"],
            auth_format=data["format"],
            signature_payload=data["payload"],
            handler_user_id=1,
        ),
        200,
    )


@bp.post("/<int:key_id>/return")
@bp.input(KeyReturnSchema)
def return_key(key_id, data):
    """Kulcs visszavétele és a státusz frissítése (Portás/Operátor)"""
    return (
        return_key_action(
            key_id=key_id,
            reservation_id=data["reservation_id"],
            receiver_id=data["receiver_id"],
            auth_format=data["format"],
            signature_payload=data["payload"],
            handler_user_id=1,
        ),
        200,
    )
