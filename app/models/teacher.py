"""
Teacher profile model.

One-to-one with User (role='teacher').
A teacher may only manage subjects they are explicitly assigned to.
"""

from datetime import datetime, timezone
from app.database.db import db
from app.models.subject import teacher_subjects


class Teacher(db.Model):
    __tablename__ = "teachers"

    # ── Primary key ────────────────────────────────────────────────────────
    id = db.Column(db.Integer, primary_key=True)

    # ── Human-readable ID ─────────────────────────────────────────────────
    teacher_id = db.Column(db.String(20), unique=True, nullable=False)  # TCH-2024-001

    # ── Auth link (one-to-one) ─────────────────────────────────────────────
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    user = db.relationship("User", back_populates="teacher_profile")

    # ── Personal info ─────────────────────────────────────────────────────
    name        = db.Column(db.String(150), nullable=False)
    phone       = db.Column(db.String(20),  nullable=True)
    designation = db.Column(db.String(100), nullable=True)  # e.g. "Assistant Professor"
    bio         = db.Column(db.Text,        nullable=True)
    profile_picture = db.Column(db.String(255), nullable=True)

    # ── Academic info ─────────────────────────────────────────────────────
    department_id = db.Column(
        db.Integer, db.ForeignKey("departments.id"), nullable=False
    )
    department = db.relationship("Department", back_populates="teachers")

    # ── Subjects this teacher is authorised to manage ─────────────────────
    subjects = db.relationship(
        "Subject",
        secondary=teacher_subjects,
        backref=db.backref("teachers", lazy="dynamic"),
        lazy="select",
    )

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

    def teaches_subject(self, subject_id: int) -> bool:
        """Return True if this teacher is authorised to manage the subject."""
        return any(s.id == subject_id for s in self.subjects)

    @property
    def pending_grading_count(self) -> int:
        from app.models.assignment import Assignment, AssignmentSubmission
        return (
            AssignmentSubmission.query.join(Assignment)
            .filter(
                Assignment.teacher_id == self.id,
                AssignmentSubmission.marks_obtained == None,  # noqa: E711
            )
            .count()
        )

    @property
    def pending_replacement_requests_count(self) -> int:
        return self.received_replacements.filter_by(status="Pending").count()

    @property
    def overall_target_progress(self) -> float:
        targets = self.targets.all()
        if not targets:
            return 75.0  # sensible default baseline
        return round(sum(t.progress_percentage for t in targets) / len(targets), 1)

    def __repr__(self) -> str:
        return f"<Teacher {self.teacher_id!r} {self.name!r}>"

