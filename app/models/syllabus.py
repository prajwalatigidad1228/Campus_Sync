"""Syllabus model."""

from datetime import datetime, timezone
from app.database.db import db


class Syllabus(db.Model):
    __tablename__ = "syllabi"

    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(
        db.Integer, db.ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False
    )
    unit_number = db.Column(db.Integer, nullable=False)
    unit_title = db.Column(db.String(200), nullable=False)
    topics = db.Column(db.Text, nullable=False)
    hours_allocated = db.Column(db.Integer, nullable=False, default=8)
    completion_status = db.Column(
        db.String(20), nullable=False, default="Pending"
    )  # 'Pending', 'In Progress', 'Completed'
    resources = db.Column(db.Text, nullable=True)

    __table_args__ = (
        db.UniqueConstraint("subject_id", "unit_number", name="uq_subject_unit"),
    )

    # Relationships
    subject = db.relationship(
        "Subject",
        backref=db.backref("syllabus_units", lazy="dynamic", cascade="all, delete-orphan"),
    )

    def __repr__(self) -> str:
        return f"<Syllabus subj={self.subject_id} unit={self.unit_number}: {self.unit_title!r}>"
