"""Assignment and AssignmentSubmission models."""

from datetime import datetime, timezone
from app.database.db import db


class Assignment(db.Model):
    __tablename__ = "assignments"

    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(
        db.Integer, db.ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False
    )
    teacher_id = db.Column(
        db.Integer, db.ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False
    )
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.DateTime, nullable=False)
    max_marks = db.Column(db.Float, nullable=False, default=100.0)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    subject = db.relationship("Subject", backref=db.backref("assignments", lazy="dynamic"))
    teacher = db.relationship("Teacher", backref=db.backref("assignments", lazy="dynamic"))
    submissions = db.relationship(
        "AssignmentSubmission",
        back_populates="assignment",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Assignment {self.id}: {self.title!r}>"


class AssignmentSubmission(db.Model):
    __tablename__ = "assignment_submissions"

    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(
        db.Integer, db.ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False
    )
    student_id = db.Column(
        db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    submission_text = db.Column(db.Text, nullable=True)
    attachment_url = db.Column(db.String(255), nullable=True)
    submitted_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    marks_obtained = db.Column(db.Float, nullable=True)
    feedback = db.Column(db.Text, nullable=True)
    graded_at = db.Column(db.DateTime(timezone=True), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="Submitted")  # Submitted, Graded, Late

    __table_args__ = (
        db.UniqueConstraint("assignment_id", "student_id", name="uq_assignment_student"),
    )

    # Relationships
    assignment = db.relationship("Assignment", back_populates="submissions")
    student = db.relationship(
        "Student",
        backref=db.backref("assignment_submissions", lazy="dynamic", cascade="all, delete-orphan"),
    )

    def __repr__(self) -> str:
        return f"<AssignmentSubmission assign={self.assignment_id} student={self.student_id} marks={self.marks_obtained}>"
