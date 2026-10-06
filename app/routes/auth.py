"""
Authentication routes for Campus_Sync.

Provides:
  /login        (GET, POST)
  /logout       (GET)
  /auth/login   (Alias for /login)
  /auth/logout  (Alias for /logout)
  /auth/me      (JSON current user details)
"""

from flask import (
    Blueprint, render_template, redirect, url_for,
    request, flash, jsonify, session
)
from flask_login import login_user, logout_user, login_required, current_user

from app.models.user import User

auth_bp = Blueprint("auth", __name__)


# ── Login ─────────────────────────────────────────────────────────────────

@auth_bp.route("/auth/login", methods=["GET", "POST"])
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    GET  – render login form.
    POST – validate credentials, establish session, redirect by role.
    """
    if current_user.is_authenticated:
        if current_user.is_student:
            return redirect(url_for("dashboard.student_dashboard"))
        elif current_user.is_teacher:
            return redirect(url_for("dashboard.teacher_dashboard"))
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash("Invalid email or password. Please try again.", "error")
            return render_template("auth/login.html"), 401

        if not user.is_active:
            flash("Your account has been deactivated. Contact the administrator.", "error")
            return render_template("auth/login.html"), 403

        # Session Fixation Defense: clear pre-existing session before authenticating
        session.clear()
        login_user(user, remember=remember)

        next_page = request.args.get("next")
        # Strict Open Redirect defense: reject protocol-relative (//) and backslash redirects
        if (
            next_page
            and next_page.startswith("/")
            and not next_page.startswith("//")
            and "\\" not in next_page
        ):
            return redirect(next_page)

        if user.is_student:
            return redirect(url_for("dashboard.student_dashboard"))
        elif user.is_teacher:
            return redirect(url_for("dashboard.teacher_dashboard"))

        return redirect(url_for("dashboard.index"))

    return render_template("auth/login.html")


# ── Logout ────────────────────────────────────────────────────────────────

@auth_bp.route("/auth/logout")
@auth_bp.route("/logout")
@login_required
def logout():
    """Clear user session and redirect to login page."""
    session.clear()
    logout_user()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("auth.login"))



# ── Debug: Current User Details ───────────────────────────────────────────

@auth_bp.route("/auth/me")
@auth_bp.route("/me")
@login_required
def me():
    """Return current authenticated user profile as JSON."""
    profile = current_user.profile
    return jsonify({
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role),
        "display_name": current_user.display_name,
        "is_active": current_user.is_active,
        "profile_id": profile.id if profile else None,
    })
