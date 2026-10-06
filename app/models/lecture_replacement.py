"""LectureReplacementRequest model."""

from datetime import datetime, timezone
from app.database.db import db


class LectureReplacementRequest(db.Model):
    __tablename__ = "lecture_replacement_requests"

    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(
        db.Integer, db.ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False
    )
    substitute_id = db.Column(
        db.Integer, db.ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False
    )
    subject_id = db.Column(
        db.Integer, db.ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False
    )
    date = db.Column(db.Date, nullable=False)
    time_slot = db.Column(db.String(50), nullable=False)  # e.g. "11:00 AM - 12:00 PM"
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Pending")  # Pending, Approved, Rejected

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    reviewed_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # Relationships
    requester = db.relationship(
        "Teacher",
        foreign_keys=[requester_id],
        backref=db.backref("sent_replacements", lazy="dynamic"),
    )
    substitute = db.relationship(
        "Teacher",
        foreign_keys=[substitute_id],
        backref=db.backref("received_replacements", lazy="dynamic"),
    )
    subject = db.relationship(
        "Subject",
        backref=db.backref("replacement_requests", lazy="dynamic"),
    )

    def __repr__(self) -> str:
        return f"<LectureReplacement req={self.requester_id} sub={self.substitute_id} status={self.status}>"
