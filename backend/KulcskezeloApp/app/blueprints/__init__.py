from apiflask import APIBlueprint
bp = APIBlueprint('main', __name__, tag="main")
from app.models import *
from apiflask import HTTPError
from app.extensions import auth
from flask import current_app
from datetime import datetime
from authlib.jose import jwt
from functools import wraps

@bp.route('/')
def index():
    return 'This is The Main Blueprint'

@auth.verify_token
def verify_token(token):
    try:
        data = jwt.decode(
            token.encode('ascii'),
            current_app.config['SECRET_KEY']
        )
        if data["exp"] < int(datetime.now().timestamp()):
            return None
        return data
    except Exception as ex:
        print(f"JWT Error: {ex}")
        return None

def role_required(roles):
    def wrapper(fn):
        @wraps(fn)
        def decorated_function(*args, **kwargs):
            user_roles = [item.get("rolename") if isinstance(item, dict) else item for item in auth.current_user.get("roles", [])]
            
            #teszteléshez
            print(f"DEBUG: Elvárt: {roles}, User roles: {user_roles}")
            
            for role in roles:
                if role in user_roles:
                    return fn(*args, **kwargs)

            raise HTTPError(message="Access denied.", status_code=403)
            
        return decorated_function
    return wrapper
