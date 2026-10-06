"""
Campus_Sync Configuration System
Each class maps to a FLASK_ENV value.
"""

import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class BaseConfig:
    """Settings shared across all environments."""

    # ── Security ───────────────────────────────────────────────────────────
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-change-me")

    # ── Session / Flask-Login ──────────────────────────────────────────────
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "Lax"
    REMEMBER_COOKIE_DURATION: timedelta = timedelta(days=7)
    # Flask-Login: the endpoint name for the login view
    LOGIN_VIEW: str = "auth.login"

    # ── Database ───────────────────────────────────────────────────────────
    # Prefer PostgreSQL (DATABASE_URL); fall back to SQLite for local dev.
    _db_url = os.getenv("DATABASE_URL")
    _sqlite_path = BASE_DIR / os.getenv("SQLITE_DB_PATH", "campus_sync.db")
    SQLALCHEMY_DATABASE_URI: str = _db_url or f"sqlite:///{_sqlite_path}"
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    # ── Uploads ────────────────────────────────────────────────────────────
    UPLOAD_FOLDER: str = str(BASE_DIR / os.getenv("UPLOAD_FOLDER", "uploads"))
    MAX_CONTENT_LENGTH: int = (
        int(os.getenv("MAX_CONTENT_LENGTH_MB", 10)) * 1024 * 1024
    )
    ALLOWED_EXTENSIONS: set = {"pdf", "png", "jpg", "jpeg", "txt", "docx", "zip"}

    # ── CORS ───────────────────────────────────────────────────────────────
    # In production, restrict to configured domains rather than wildcard *
    CORS_ORIGINS: list = (
        os.getenv("CORS_ORIGINS", "http://localhost:5000,http://127.0.0.1:5000").split(",")
    )


    # ── App meta ───────────────────────────────────────────────────────────
    APP_NAME: str = "Campus_Sync"
    APP_VERSION: str = "1.0.0"


class DevelopmentConfig(BaseConfig):
    DEBUG: bool = True
    TESTING: bool = False
    SESSION_COOKIE_SECURE: bool = False   # no HTTPS in dev


class TestingConfig(BaseConfig):
    DEBUG: bool = True
    TESTING: bool = True
    WTF_CSRF_ENABLED: bool = False
    SESSION_COOKIE_SECURE: bool = False
    # Always use in-memory SQLite for tests
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///:memory:"


class ProductionConfig(BaseConfig):
    DEBUG: bool = False
    TESTING: bool = False
    SESSION_COOKIE_SECURE: bool = True   # HTTPS only in prod

    # In production the DATABASE_URL env-var must be set.
    @classmethod
    def validate(cls):
        if not os.getenv("DATABASE_URL"):
            raise RuntimeError("DATABASE_URL must be set in production.")
        if os.getenv("SECRET_KEY", "dev-secret-change-me") == "dev-secret-change-me":
            raise RuntimeError("SECRET_KEY must be changed in production.")


CONFIG_MAP: dict = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
