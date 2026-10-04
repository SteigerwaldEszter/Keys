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
    """A rendszerben nyilvántartott felhasználók listázása."""
    success, res = UserService.get_all_users()
    if success:
        return res
    raise HTTPError(400, res)


@bp.get("/<int:id>")
@bp.auth_required(auth)
@role_required(["Admin"])
@bp.output(UserSchema)
def get_user_by_id(id):
    """Felhasználó lekérdezése azonosító alapján."""
    success, res = UserService.get_user_by_id(id)
    if success:
        return res
    raise HTTPError(404, res)


@bp.put("/update/<int:id>")
@bp.auth_required(auth)
@role_required(["Admin"])
@bp.input(RoleUpdateSchema)
def update_user_roles(id, json_data):
    """Felhasználó szerepkörének frissítése."""
    success, res = UserService.update_user_roles(id, json_data)
    if success:
        return res
    raise HTTPError(400, res)
