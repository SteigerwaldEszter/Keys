from apiflask import APIBlueprint, HTTPError

from app.blueprints import role_required
from app.blueprints.users.schemas import (
    RoleUpdateSchema,
    UserListResponseSchema,
    UserSchema,
)
from app.blueprints.users.service import UserService
from app.extensions import auth

bp = APIBlueprint("users", __name__, tag="users")


@bp.route("/")
def index():
    return "This is The Users Blueprint"


@bp.get("/list")
@bp.auth_required(auth)
@role_required(["Admin"])
@bp.output(UserListResponseSchema)
def get_users():
    success, res = UserService.get_all_users()

    if success:
        return res

    raise HTTPError(400, res)


@bp.get("/<int:id>")
@bp.auth_required(auth)
@role_required(["Admin"])
@bp.output(UserSchema)
def get_user_by_id(id):
    success, res = UserService.get_user_by_id(id)

    if success:
        return res

    raise HTTPError(404, res)


@bp.put("/update/<int:id>")
@bp.auth_required(auth)
@role_required(["Admin"])
@bp.input(RoleUpdateSchema)
def update_user_roles(id, json_data):
    success, res = UserService.update_user_roles(
        user_id=id,
        json_data=json_data,
        actor_user_id=auth.current_user["user_id"],
    )

    if success:
        return res

    raise HTTPError(400, res)
