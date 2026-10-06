"""Department model."""

from app.database.db import db


class Department(db.Model):
    __tablename__ = "departments"

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(150), unique=True, nullable=False)
    code        = db.Column(db.String(10),  unique=True, nullable=False)  # e.g. "CS", "ME"
    description = db.Column(db.Text, nullable=True)

    # Back-references
    students = db.relationship("Student", back_populates="department", lazy="dynamic")
    teachers = db.relationship("Teacher", back_populates="department", lazy="dynamic")
    subjects = db.relationship("Subject", back_populates="department", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<Department {self.code!r}>"
