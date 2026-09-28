from apiflask import APIBlueprint

bp = APIBlueprint('auth', __name__, tag="auth")

from app.blueprints.auth import routes