"""Fee model."""

from datetime import datetime, timezone
from app.database.db import db


class Fee(db.Model):
    __tablename__ = "fees"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    title = db.Column(db.String(150), nullable=False)
    fee_type = db.Column(db.String(50), nullable=False, default="Tuition")  # Tuition, Exam, Library, Laboratory
    amount = db.Column(db.Float, nullable=False)
    amount_paid = db.Column(db.Float, nullable=False, default=0.0)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Pending")  # Paid, Pending, Overdue, Partial
    receipt_number = db.Column(db.String(50), unique=True, nullable=True)
    paid_at = db.Column(db.DateTime(timezone=True), nullable=True)
    semester = db.Column(db.Integer, nullable=True)
    academic_year = db.Column(db.String(20), nullable=True)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    student = db.relationship("Student", backref=db.backref("fees", lazy="dynamic", cascade="all, delete-orphan"))

    @property
    def remaining_balance(self) -> float:
        return max(0.0, self.amount - self.amount_paid)

    def __repr__(self) -> str:
        return f"<Fee {self.id}: {self.title!r} amt={self.amount} status={self.status}>"
