"""TeacherTarget model."""

from datetime import datetime, timezone
from app.database.db import db


class TeacherTarget(db.Model):
    __tablename__ = "teacher_targets"

    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(
        db.Integer, db.ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False
    )
    subject_id = db.Column(
        db.Integer, db.ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False
    )
    target_title = db.Column(db.String(200), nullable=False)
    planned_lectures = db.Column(db.Integer, nullable=False, default=10)
    completed_lectures = db.Column(db.Integer, nullable=False, default=0)
    target_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="On Track")  # On Track, Behind, Completed
    remarks = db.Column(db.Text, nullable=True)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    teacher = db.relationship(
        "Teacher",
        backref=db.backref("targets", lazy="dynamic", cascade="all, delete-orphan"),
    )
    subject = db.relationship(
        "Subject",
        backref=db.backref("teacher_targets", lazy="dynamic"),
    )

    @property
    def progress_percentage(self) -> float:
        if self.planned_lectures <= 0:
            return 100.0 if self.completed_lectures > 0 else 0.0
        return min(100.0, round((self.completed_lectures / self.planned_lectures) * 100, 1))

    def __repr__(self) -> str:
        return f"<TeacherTarget teacher={self.teacher_id} subj={self.subject_id} {self.target_title!r}>"
