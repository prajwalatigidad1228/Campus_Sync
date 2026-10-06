"""Subject model."""

from app.database.db import db

# Association table: many Teachers <-> many Subjects
teacher_subjects = db.Table(
    "teacher_subjects",
    db.Column("teacher_id", db.Integer, db.ForeignKey("teachers.id"), primary_key=True),
    db.Column("subject_id", db.Integer, db.ForeignKey("subjects.id"), primary_key=True),
)


class Subject(db.Model):
    __tablename__ = "subjects"

    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(150), nullable=False)
    code          = db.Column(db.String(20),  nullable=False)   # e.g. "CS301"
    semester      = db.Column(db.Integer, nullable=True)         # 1–8
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=False)

    department = db.relationship("Department", back_populates="subjects")

    __table_args__ = (
        db.UniqueConstraint("code", "department_id", name="uq_subject_code_dept"),
    )

    def __repr__(self) -> str:
        return f"<Subject {self.code!r} sem={self.semester}>"
