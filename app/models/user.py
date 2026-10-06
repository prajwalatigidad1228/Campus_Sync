"""
User model – the single source of authentication identity.

Every person in the system (Student or Teacher) has exactly one User row.
Role-specific profile data lives in the Student / Teacher tables.
"""

import enum
from datetime import datetime, timezone
from flask_login import UserMixin
from app.database.db import db, bcrypt


class Role(str, enum.Enum):
    STUDENT = "student"
    TEACHER = "teacher"


class User(UserMixin, db.Model):
    """Authentication identity shared by all roles."""

    __tablename__ = "users"

    # ── Primary key ────────────────────────────────────────────────────────
    id = db.Column(db.Integer, primary_key=True)

    # ── Identity ───────────────────────────────────────────────────────────
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    # ── Role ───────────────────────────────────────────────────────────────
    role = db.Column(
        db.Enum(Role, name="user_role"),
        nullable=False,
    )

    # ── Status ─────────────────────────────────────────────────────────────
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # ── Timestamps ─────────────────────────────────────────────────────────
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ── Back-references (populated by Student / Teacher models) ───────────
    student_profile = db.relationship(
        "Student", back_populates="user", uselist=False, lazy="select"
    )
    teacher_profile = db.relationship(
        "Teacher", back_populates="user", uselist=False, lazy="select"
    )

    # ── Password helpers ──────────────────────────────────────────────────
    def set_password(self, plain_text: str) -> None:
        """Hash and store the password. Never store plain text."""
        self.password_hash = bcrypt.generate_password_hash(plain_text).decode("utf-8")

    def check_password(self, plain_text: str) -> bool:
        """Return True if the given password matches the stored hash."""
        return bcrypt.check_password_hash(self.password_hash, plain_text)

    # ── Flask-Login: is_active property ───────────────────────────────────
    def get_id(self) -> str:
        """Flask-Login requires a string user id."""
        return str(self.id)

    # ── Role helpers ───────────────────────────────────────────────────────
    @property
    def is_student(self) -> bool:
        return self.role == Role.STUDENT

    @property
    def is_teacher(self) -> bool:
        return self.role == Role.TEACHER

    @property
    def profile(self):
        """Return the role-specific profile object or None."""
        if self.is_student:
            return self.student_profile
        if self.is_teacher:
            return self.teacher_profile
        return None

    @property
    def display_name(self) -> str:
        """Return the user friendly name for use in templates."""
        p = self.profile
        return p.name if p else self.email.split("@")[0]

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role}>"
