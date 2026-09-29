from apiflask import HTTPError
from app.blueprints.auth import bp
from app.extensions import auth
from app.blueprints.auth.schemas import (
    UserLoginSchema,
    RegisterRequestSchema,
    TokenResponseSchema,
    UserResponseSchema,
)
from app.blueprints.auth.service import AuthService


@bp.route("/")
def index():
    return "This is The Auth Blueprint"


@bp.post("/register")
@bp.auth_required(auth)
@role_required(["Admin"])
@bp.input(RegisterRequestSchema)
@bp.output(UserResponseSchema)
def register(json_data):
    success, res = AuthService.register(json_data)
    if success:
        return res
    raise HTTPError(400, res)


@bp.post("/login")
@bp.input(UserLoginSchema)
@bp.output(TokenResponseSchema)
def login(json_data):
    success, res = AuthService.login(json_data)
    if success:
        return res
    raise HTTPError(401, res)


@bp.post("/logout")
@bp.auth_required(auth)
def logout():
    return {"message": "Sikeres kijelentkezés"}, 200


@bp.get("/me")
@bp.auth_required(auth)
def get_me():
    from app.models.user import User

    user = User.query.get(auth.current_user["user_id"])
    return {"id": user.id, "name": user.name, "roles": [r.role for r in user.roles]}
