"""ExamTimetable model."""

from datetime import datetime, timezone
from app.database.db import db


class ExamTimetable(db.Model):
    __tablename__ = "exam_timetables"

    id = db.Column(db.Integer, primary_key=True)
    department_id = db.Column(
        db.Integer, db.ForeignKey("departments.id", ondelete="CASCADE"), nullable=False
    )
    subject_id = db.Column(
        db.Integer, db.ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False
    )
    exam_name = db.Column(db.String(150), nullable=False)
    exam_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.String(20), nullable=False)  # e.g. "10:00 AM"
    end_time = db.Column(db.String(20), nullable=False)    # e.g. "01:00 PM"
    room_number = db.Column(db.String(50), nullable=False) # e.g. "Hall 302"
    semester = db.Column(db.Integer, nullable=False)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    department = db.relationship("Department", backref=db.backref("exam_timetables", lazy="dynamic"))
    subject = db.relationship("Subject", backref=db.backref("exam_timetables", lazy="dynamic"))

    def __repr__(self) -> str:
        return f"<ExamTimetable {self.exam_name!r} subj={self.subject_id} date={self.exam_date}>"
