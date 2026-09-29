from apiflask import APIBlueprint

bp = APIBlueprint("auth", __name__, tag="auth")

from . import routes  # noqa: E402, F401
