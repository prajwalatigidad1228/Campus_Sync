"""
Health / status routes.
Used by monitoring, CI, and Docker health-checks.
"""

import platform
from flask import Blueprint, jsonify, current_app
from app.utils.helpers import get_timestamp

health_bp = Blueprint("health", __name__, url_prefix="/api")


@health_bp.route("/health", methods=["GET"])
def health_check():
    """
    Basic health-check endpoint.
    Returns 200 with system info when the app is running correctly.
    """
    return jsonify(
        {
            "status": "ok",
            "app": current_app.config.get("APP_NAME", "Campus_Sync"),
            "version": current_app.config.get("APP_VERSION", "1.0.0"),
            "timestamp": get_timestamp(),
            "python": platform.python_version(),
            "environment": current_app.config.get("ENV", "unknown"),
        }
    ), 200


@health_bp.route("/status", methods=["GET"])
def status():
    """Extended status – checks DB connectivity."""
    from app.database.db import db
    db_ok = False
    db_error = None
    try:
        db.session.execute(db.text("SELECT 1"))
        db_ok = True
    except Exception as exc:
        db_error = str(exc)

    payload = {
        "status": "ok" if db_ok else "degraded",
        "database": "connected" if db_ok else f"error: {db_error}",
        "timestamp": get_timestamp(),
    }
    status_code = 200 if db_ok else 503
    return jsonify(payload), status_code
