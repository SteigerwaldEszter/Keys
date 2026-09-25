from apiflask import APIFlask
from config import Config
from app.extensions import db, migrate
from app import models

def create_app(config_class=Config):
    app = APIFlask(__name__, json_errors=True, docs_path="/swagger", title="Raktar API")
    app.config.from_object(config_class)

    #Extensions
    db.init_app(app)
    migrate.init_app(app, db)


    #Blueprints
    #from app.blueprints import bp as bp_default
    #app.register_blueprint(bp_default, url_prefix='/api')

    return app
