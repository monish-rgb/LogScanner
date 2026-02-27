import os
from flask import Flask
from flask_cors import CORS

from .extensions import db, jwt, bcrypt, migrate


def create_app(config_name=None):
    app = Flask(__name__)

    config_map = {
        "development": "config.DevelopmentConfig",
        "production": "config.ProductionConfig",
        "testing": "config.TestingConfig",
    }
    config_key = config_name or os.environ.get("FLASK_ENV", "development")
    app.config.from_object(config_map.get(config_key, "config.DevelopmentConfig"))

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)

    from .blueprints.auth import auth_bp
    from .blueprints.upload import upload_bp
    from .blueprints.dashboard import dashboard_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(upload_bp, url_prefix="/api")
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")

    from .middleware.error_handlers import register_error_handlers
    register_error_handlers(app)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    return app
