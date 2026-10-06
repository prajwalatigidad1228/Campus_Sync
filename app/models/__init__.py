"""
Models package.
All models imported here so Flask-Migrate / db.create_all() can detect them.
Import order matters: parent entities before child entities with foreign keys.
"""

from app.models.user import User, Role
from app.models.department import Department
from app.models.subject import Subject, teacher_subjects
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.attendance import Attendance
from app.models.assignment import Assignment, AssignmentSubmission
from app.models.fee import Fee
from app.models.announcement import Announcement
from app.models.syllabus import Syllabus
from app.models.target import TeacherTarget
from app.models.test import Test, Question, TestAttempt, TestAnswer
from app.models.exam import ExamTimetable
from app.models.result import Result
from app.models.feedback import Feedback
from app.models.lecture_replacement import LectureReplacementRequest
from app.models.upload import FileUpload

__all__ = [
    "User",
    "Role",
    "Department",
    "Subject",
    "teacher_subjects",
    "Student",
    "Teacher",
    "Attendance",
    "Assignment",
    "AssignmentSubmission",
    "Fee",
    "Announcement",
    "Syllabus",
    "TeacherTarget",
    "Test",
    "Question",
    "TestAttempt",
    "TestAnswer",
    "ExamTimetable",
    "Result",
    "Feedback",
    "LectureReplacementRequest",
    "FileUpload",
]

