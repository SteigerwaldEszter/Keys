# from datetime import datetime
# from functools import wraps

# from apiflask import apiblueprint, httperror
# from authlib.jose import jwt
# from flask import current_app

# from app.extensions import auth

# bp = apiblueprint("main", __name__, tag="main")


# @bp.route("/")
# def index():
#     return "this is the main blueprint"


# @auth.verify_token
# def verify_token(token):
#     try:
#         data = jwt.decode(
#             token.encode("ascii"),
#             current_app.config["secret_key"],
#         )
#         if data["exp"] < int(datetime.now().timestamp()):
#             return none
#         return data
#     except exception as ex:
#         print(f"jwt error: {ex}")
#         return none


# def role_required(roles):
#     def wrapper(fn):
#         @wraps(fn)
#         def decorated_function(*args, **kwargs):
#             user_roles = [
#                 item.get("rolename") if isinstance(item, dict) else item
#                 for item in auth.current_user.get("roles", [])
#             ]

#             # teszteléshez
#             print(f"debug: elvárt: {roles}, user roles: {user_roles}")

#             for role in roles:
#                 if role in user_roles:
#                     return fn(*args, **kwargs)

#             raise httperror(message="access denied.", status_code=403)

#         return decorated_function

#     return wrapper