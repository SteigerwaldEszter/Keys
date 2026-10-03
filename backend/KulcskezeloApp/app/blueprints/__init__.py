from datetime import datetime
from functools import wraps

from apiflask import APIBlueprint, HTTPError
from authlib.jose import jwt
from flask import current_app

from app.extensions import auth as token_auth

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
        return data
    except Exception as ex:
        print(f"jwt error: {ex}")
        return None


def role_required(roles):
    def wrapper(fn):
        @wraps(fn)
        def decorated_function(*args, **kwargs):
            user_roles = [
                item.get("role") if isinstance(item, dict) else item
                for item in token_auth.current_user.get("roles", [])
            ]

            # Teszteléshez
            print(f"debug: elvárt: {roles}, user roles: {user_roles}")

            for role in roles:
                if role in user_roles:
                    return fn(*args, **kwargs)

            raise HTTPError(message="access denied.", status_code=403)

        return decorated_function

    return wrapper
