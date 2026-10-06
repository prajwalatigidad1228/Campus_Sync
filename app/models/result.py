"""Result model."""

from datetime import datetime, timezone
from app.database.db import db


class Result(db.Model):
    __tablename__ = "results"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    subject_id = db.Column(
        db.Integer, db.ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False
    )
    exam_name = db.Column(db.String(150), nullable=False)
    internal_marks = db.Column(db.Float, nullable=False, default=0.0)
    external_marks = db.Column(db.Float, nullable=False, default=0.0)
    total_marks = db.Column(db.Float, nullable=False, default=0.0)
    max_marks = db.Column(db.Float, nullable=False, default=100.0)
    grade = db.Column(db.String(5), nullable=False)  # e.g. "O", "A+", "A", "B+", "B", "F"
    status = db.Column(db.String(10), nullable=False, default="Pass")  # "Pass" or "Fail"
    semester = db.Column(db.Integer, nullable=False)
    academic_year = db.Column(db.String(20), nullable=False)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    student = db.relationship("Student", backref=db.backref("results", lazy="dynamic", cascade="all, delete-orphan"))
    subject = db.relationship("Subject", backref=db.backref("results", lazy="dynamic"))

    @property
    def percentage(self) -> float:
        if not self.max_marks:
            return 0.0
        return round((self.total_marks / self.max_marks) * 100, 1)

    def __repr__(self) -> str:
        return f"<Result student={self.student_id} subj={self.subject_id} total={self.total_marks} grade={self.grade}>"
