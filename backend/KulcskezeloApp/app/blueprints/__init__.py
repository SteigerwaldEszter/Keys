from datetime import datetime
from functools import wraps

from apiflask import APIBlueprint, HTTPError
from authlib.jose import jwt
from flask import current_app, request

from app.extensions import auth as token_auth
from app.extensions import db
from app.models.user import User

bp = APIBlueprint("main", __name__, tag="main")


@bp.route("/")
def index():
    return "this is the main blueprint"


@token_auth.verify_token
def verify_token(token):
    try:
        data = jwt.decode(
            token.encode("ascii"),
            current_app.config["PRIVATE_KEY"],
        )

        if data["exp"] < int(datetime.now().timestamp()):
            return None

        user_id = data.get("user_id")

        if not isinstance(user_id, int):
            return None

        user = db.session.get(User, user_id)

        if user is None or not user.is_active:
            return None

        return {
            "user_id": user.id,
            "roles": [role.name for role in user.roles],
        }

    except Exception:
        current_app.logger.exception("Token verification failed")
        return None


def role_required(roles):
    allowed_roles = {roles} if isinstance(roles, str) else set(roles)

    def wrapper(fn):
        @wraps(fn)
        def decorated_function(*args, **kwargs):
            current_user = token_auth.current_user

            if not isinstance(current_user, dict):
                raise HTTPError(
                    message="Authentication required.",
                    status_code=401,
                )

            user_roles = set(current_user.get("roles", []))

            if not allowed_roles.intersection(user_roles):
                try:
                    from app.blueprints.reports.service import (
                        create_audit_log,
                    )

                    create_audit_log(
                        action="ACCESS_DENIED",
                        entity_name="authorization",
                        entity_value=request.endpoint,
                        user_id=current_user["user_id"],
                        new_value={
                            "method": request.method,
                            "path": request.path,
                            "required_roles": sorted(allowed_roles),
                            "user_roles": sorted(user_roles),
                            "reason": "insufficient_permissions",
                        },
                    )

                    db.session.commit()

                except Exception:
                    db.session.rollback()
                    current_app.logger.exception("Access denied audit logging failed")

                raise HTTPError(
                    message="Access denied.",
                    status_code=403,
                )

            return fn(*args, **kwargs)

        return decorated_function

    return wrapper
