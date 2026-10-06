"""
Campus_Sync – Application Factory
"""

import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

# Load .env before anything else
load_dotenv()


def create_app(config_name: str = "development") -> Flask:
    """
    Flask application factory.

    Args:
        config_name: One of 'development', 'testing', or 'production'.

    Returns:
        A fully configured Flask application instance.
    """
    from app.config import CONFIG_MAP

    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "..", "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "..", "static"),
    )

    # ── Load configuration ─────────────────────────────────────────────────
    cfg_class = CONFIG_MAP.get(config_name, CONFIG_MAP["development"])
    app.config.from_object(cfg_class)
    app.config["ENV"] = config_name

    # ── Extensions ─────────────────────────────────────────────────────────
    CORS(app, origins=app.config.get("CORS_ORIGINS", ["*"]))

    # Init DB, Flask-Login, Bcrypt (all in one call)
    from app.database import init_db
    init_db(app)

    # ── Ensure upload folder exists ────────────────────────────────────────
    from app.utils.helpers import ensure_dir
    ensure_dir(app.config["UPLOAD_FOLDER"])

    # ── Register security headers hook ─────────────────────────────────────
    from app.utils.security_headers import init_security_headers
    init_security_headers(app)

    # ── Register blueprints ────────────────────────────────────────────────
    _register_blueprints(app)

    # ── Register error handlers ────────────────────────────────────────────
    from app.utils.error_handlers import register_error_handlers
    register_error_handlers(app)

    # ── Create all tables (development / testing only) ─────────────────────
    if config_name in ("development", "testing"):
        # Import all models so SQLAlchemy knows about them before create_all()
        from . import models  # noqa: F401
        from app.database.db import db
        with app.app_context():
            db.create_all()

    return app


def _register_blueprints(app: Flask) -> None:
    """Register all route blueprints."""
    from app.routes.main import main_bp
    from app.routes.health import health_bp
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.college_api import college_api_bp
    from app.routes.copilot_api import copilot_api_bp
    from app.routes.upload_api import upload_api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(college_api_bp)
    app.register_blueprint(copilot_api_bp)
    app.register_blueprint(upload_api_bp)



