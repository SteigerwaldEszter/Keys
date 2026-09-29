from apiflask import APIFlask
from config import Config
from flask_migrate import Migrate

from app.extensions import db


def create_app(config_class=Config):
    app = APIFlask(
        __name__, json_errors=True, docs_path="/swagger", title="Kulcskezelo API"
    )
    app.config.from_object(config_class)

    # Extensions
    db.init_app(app)
    Migrate(app, db)

    # Blueprints
    from app.blueprints import bp as bp_default
    from app.blueprints.auth import bp as bp_auth

    app.register_blueprint(bp_default, url_prefix="/api")
    app.register_blueprint(bp_auth, url_prefix="/api/auth")

    return app
