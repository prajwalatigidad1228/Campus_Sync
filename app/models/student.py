"""
Student profile model.

One-to-one with User (role='student').
Security rule: a student can only access their OWN profile.
Check enforced in routes/dashboard.py via @owns_profile decorator.
"""

from datetime import datetime, timezone
from app.database.db import db


class Student(db.Model):
    __tablename__ = "students"

    # ── Primary key ────────────────────────────────────────────────────────
    id = db.Column(db.Integer, primary_key=True)

    # ── Human-readable ID ─────────────────────────────────────────────────
    student_id = db.Column(db.String(20), unique=True, nullable=False)  # STU-2024-001

    # ── Auth link (one-to-one) ─────────────────────────────────────────────
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    user = db.relationship("User", back_populates="student_profile")

    # ── Personal info ─────────────────────────────────────────────────────
    name         = db.Column(db.String(150), nullable=False)
    phone        = db.Column(db.String(20),  nullable=True)
    address      = db.Column(db.Text,        nullable=True)
    bio          = db.Column(db.Text,        nullable=True)
    profile_picture = db.Column(db.String(255), nullable=True)

    # ── Academic info ─────────────────────────────────────────────────────
    department_id = db.Column(
        db.Integer, db.ForeignKey("departments.id"), nullable=False
    )
    semester    = db.Column(db.Integer, nullable=False, default=1)  # 1-8
    division    = db.Column(db.String(5),  nullable=True)           # A, B, C
    roll_number = db.Column(db.String(20), nullable=True)

    department = db.relationship("Department", back_populates="students")

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

    @property
    def email(self) -> str:
        return self.user.email if self.user else ""

    @property
    def attendance_percentage(self) -> float:
        total = self.attendances.count()
        if total == 0:
            return 100.0
        present = self.attendances.filter_by(status="Present").count()
        return round((present / total) * 100, 1)

    @property
    def total_lectures(self) -> int:
        return self.attendances.count()

    @property
    def present_lectures(self) -> int:
        return self.attendances.filter_by(status="Present").count()

    @property
    def absent_lectures(self) -> int:
        return self.attendances.filter_by(status="Absent").count()

    @property
    def pending_fees_amount(self) -> float:
        return sum(f.remaining_balance for f in self.fees.all())

    def __repr__(self) -> str:
        return f"<Student {self.student_id!r} {self.name!r}>"

