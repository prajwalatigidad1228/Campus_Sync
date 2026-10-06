"""
Database + auth extension singletons.

Import `db`, `migrate`, `login_manager`, `bcrypt` anywhere in the app.
They are bound to the Flask app in create_app() via init_db().
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
bcrypt = Bcrypt()


def init_db(app):
    """Bind all database and auth extensions to the Flask app."""
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)

    # ── Flask-Login configuration ─────────────────────────────────────────
    login_manager.init_app(app)
    login_manager.login_view = app.config.get("LOGIN_VIEW", "auth.login")
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "warning"

    # ── User loader (required by Flask-Login) ─────────────────────────────
    # Imported inside the function to avoid circular imports at module load.
    @login_manager.user_loader
    def load_user(user_id: str):
        from app.models.user import User
        return db.session.get(User, int(user_id))
