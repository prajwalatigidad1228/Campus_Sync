"""Online Test, Question, TestAttempt, and TestAnswer models."""

from datetime import datetime, timezone
from app.database.db import db


class Test(db.Model):
    __test__ = False
    __tablename__ = "tests"


    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(
        db.Integer, db.ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False
    )
    teacher_id = db.Column(
        db.Integer, db.ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False
    )
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    duration_minutes = db.Column(db.Integer, nullable=False, default=30)
    total_marks = db.Column(db.Float, nullable=False, default=20.0)
    passing_marks = db.Column(db.Float, nullable=False, default=8.0)
    start_time = db.Column(db.DateTime(timezone=True), nullable=True)
    end_time = db.Column(db.DateTime(timezone=True), nullable=True)
    is_published = db.Column(db.Boolean, nullable=False, default=True)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    subject = db.relationship("Subject", backref=db.backref("tests", lazy="dynamic"))
    teacher = db.relationship("Teacher", backref=db.backref("tests", lazy="dynamic"))
    questions = db.relationship(
        "Question",
        back_populates="test",
        lazy="dynamic",
        cascade="all, delete-orphan",
        order_by="Question.order_index",
    )
    attempts = db.relationship(
        "TestAttempt",
        back_populates="test",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Test {self.id}: {self.title!r} duration={self.duration_minutes}m>"


class Question(db.Model):
    __tablename__ = "questions"

    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(
        db.Integer, db.ForeignKey("tests.id", ondelete="CASCADE"), nullable=False
    )
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.Text, nullable=False)
    option_b = db.Column(db.Text, nullable=False)
    option_c = db.Column(db.Text, nullable=True)
    option_d = db.Column(db.Text, nullable=True)
    correct_option = db.Column(db.String(5), nullable=False)  # 'A', 'B', 'C', 'D'
    marks = db.Column(db.Float, nullable=False, default=1.0)
    order_index = db.Column(db.Integer, nullable=False, default=0)

    # Relationships
    test = db.relationship("Test", back_populates="questions")

    def __repr__(self) -> str:
        return f"<Question {self.id} test={self.test_id}>"


class TestAttempt(db.Model):
    __test__ = False
    __tablename__ = "test_attempts"

    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(
        db.Integer, db.ForeignKey("tests.id", ondelete="CASCADE"), nullable=False
    )
    student_id = db.Column(
        db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    started_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    submitted_at = db.Column(db.DateTime(timezone=True), nullable=True)
    score = db.Column(db.Float, nullable=True)
    total_marks = db.Column(db.Float, nullable=False, default=0.0)
    status = db.Column(db.String(20), nullable=False, default="in_progress")  # in_progress, submitted, timed_out

    __table_args__ = (
        db.UniqueConstraint("test_id", "student_id", name="uq_test_student_attempt"),
    )

    # Relationships
    test = db.relationship("Test", back_populates="attempts")
    student = db.relationship(
        "Student",
        backref=db.backref("test_attempts", lazy="dynamic", cascade="all, delete-orphan"),
    )
    answers = db.relationship(
        "TestAnswer",
        back_populates="attempt",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    @property
    def percentage(self) -> float:
        if not self.total_marks or self.score is None:
            return 0.0
        return round((self.score / self.total_marks) * 100, 1)

    def __repr__(self) -> str:
        return f"<TestAttempt test={self.test_id} student={self.student_id} score={self.score}>"


class TestAnswer(db.Model):
    __test__ = False
    __tablename__ = "test_answers"


    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(
        db.Integer, db.ForeignKey("test_attempts.id", ondelete="CASCADE"), nullable=False
    )
    question_id = db.Column(
        db.Integer, db.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )
    selected_option = db.Column(db.String(5), nullable=True)
    is_correct = db.Column(db.Boolean, nullable=False, default=False)
    marks_awarded = db.Column(db.Float, nullable=False, default=0.0)

    # Relationships
    attempt = db.relationship("TestAttempt", back_populates="answers")
    question = db.relationship("Question")

    def __repr__(self) -> str:
        return f"<TestAnswer attempt={self.attempt_id} q={self.question_id} opt={self.selected_option}>"
