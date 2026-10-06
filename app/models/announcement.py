"""Announcement model."""

from datetime import datetime, timezone
from app.database.db import db


class Announcement(db.Model):
    __tablename__ = "announcements"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(
        db.String(50), nullable=False
    )  # 'College Management', 'Teachers', 'Student Coordinators'
    target_role = db.Column(
        db.String(20), nullable=False, default="all"
    )  # 'all', 'student', 'teacher'
    author_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    department_id = db.Column(
        db.Integer, db.ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )
    is_pinned = db.Column(db.Boolean, default=False, nullable=False)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    author = db.relationship("User", backref=db.backref("announcements", lazy="dynamic"))
    department = db.relationship("Department", backref=db.backref("announcements", lazy="dynamic"))

    def __repr__(self) -> str:
        return f"<Announcement {self.id}: {self.title!r} cat={self.category}>"
