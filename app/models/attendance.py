"""Attendance model."""

from datetime import datetime, timezone
from app.database.db import db


class Attendance(db.Model):
    __tablename__ = "attendances"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    subject_id = db.Column(
        db.Integer, db.ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False
    )
    teacher_id = db.Column(
        db.Integer, db.ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True
    )
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Present")  # Present, Absent, Excused, Late
    remarks = db.Column(db.String(255), nullable=True)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        db.UniqueConstraint("student_id", "subject_id", "date", name="uq_student_subject_date"),
    )

    # Relationships
    student = db.relationship("Student", backref=db.backref("attendances", lazy="dynamic", cascade="all, delete-orphan"))
    subject = db.relationship("Subject", backref=db.backref("attendances", lazy="dynamic"))
    teacher = db.relationship("Teacher", backref=db.backref("marked_attendances", lazy="dynamic"))

    def __repr__(self) -> str:
        return f"<Attendance student={self.student_id} subj={self.subject_id} date={self.date} {self.status}>"
