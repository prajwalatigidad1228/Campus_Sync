"""Feedback model."""

from datetime import datetime, timezone
from app.database.db import db


class Feedback(db.Model):
    __tablename__ = "feedbacks"

    id = db.Column(db.Integer, primary_key=True)
    feedback_type = db.Column(
        db.String(30), nullable=False
    )  # 'student_to_teacher' or 'teacher_to_management'
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    student_id = db.Column(
        db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=True
    )
    teacher_id = db.Column(
        db.Integer, db.ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True
    )
    subject_id = db.Column(
        db.Integer, db.ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True
    )
    category = db.Column(db.String(100), nullable=False)  # Teaching, Infrastructure, Curriculum, etc.
    rating = db.Column(db.Integer, nullable=False, default=5)  # 1-5
    comments = db.Column(db.Text, nullable=False)
    is_anonymous = db.Column(db.Boolean, nullable=False, default=False)
    status = db.Column(db.String(20), nullable=False, default="Submitted")  # Submitted, Reviewed

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user = db.relationship("User", backref=db.backref("feedback_submissions", lazy="dynamic"))
    student = db.relationship("Student", backref=db.backref("feedback_given", lazy="dynamic"))
    teacher = db.relationship("Teacher", backref=db.backref("feedback_received", lazy="dynamic"))
    subject = db.relationship("Subject", backref=db.backref("feedbacks", lazy="dynamic"))

    def __repr__(self) -> str:
        return f"<Feedback {self.id}: {self.feedback_type} rating={self.rating}>"
