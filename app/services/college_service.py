"""
Campus_Sync – College Management Core Service
Encapsulates all business logic, validation, and authorization checks.
"""

from datetime import datetime, timezone, date
import uuid
from typing import Dict, List, Optional, Tuple

from app.database.db import db
from app.models.user import User, Role
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.subject import Subject
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


class AuthorizationError(Exception):
    """Raised when an operation is forbidden by role or resource ownership."""
    pass


class ValidationError(Exception):
    """Raised when input validation fails."""
    pass


class CollegeService:

    # ── 1. Attendance Management ───────────────────────────────────────────

    @staticmethod
    def mark_attendance(
        teacher: Teacher,
        subject_id: int,
        attendance_date: date,
        records: List[Dict],
    ) -> List[Attendance]:
        """
        Record attendance for a class.
        Only teachers assigned to `subject_id` are authorized.
        """
        if not teacher.teaches_subject(subject_id):
            raise AuthorizationError("Teacher is not authorized to manage attendance for this subject.")

        saved_records = []
        for item in records:
            student_id = item.get("student_id")
            status = item.get("status", "Present")
            remarks = item.get("remarks")

            # Validate student exists
            student = Student.query.get(student_id)
            if not student:
                continue

            record = Attendance.query.filter_by(
                student_id=student_id,
                subject_id=subject_id,
                date=attendance_date,
            ).first()

            if record:
                record.status = status
                record.remarks = remarks
                record.teacher_id = teacher.id
            else:
                record = Attendance(
                    student_id=student_id,
                    subject_id=subject_id,
                    teacher_id=teacher.id,
                    date=attendance_date,
                    status=status,
                    remarks=remarks,
                )
                db.session.add(record)

            saved_records.append(record)

        db.session.commit()
        return saved_records

    # ── 2. Assignments & Submissions ───────────────────────────────────────

    @staticmethod
    def create_assignment(
        teacher: Teacher,
        subject_id: int,
        title: str,
        description: str,
        due_date: datetime,
        max_marks: float = 100.0,
    ) -> Assignment:
        """Create assignment by authorized teacher."""
        if not teacher.teaches_subject(subject_id):
            raise AuthorizationError("Teacher is not authorized to create assignments for this subject.")

        assignment = Assignment(
            subject_id=subject_id,
            teacher_id=teacher.id,
            title=title,
            description=description,
            due_date=due_date,
            max_marks=max_marks,
        )
        db.session.add(assignment)
        db.session.commit()
        return assignment

    @staticmethod
    def submit_assignment(
        student: Student,
        assignment_id: int,
        submission_text: str,
        attachment_url: Optional[str] = None,
    ) -> AssignmentSubmission:
        """Submit assignment by authorized student."""
        assignment = Assignment.query.get_or_404(assignment_id)

        # Check existing submission
        sub = AssignmentSubmission.query.filter_by(
            assignment_id=assignment.id,
            student_id=student.id,
        ).first()

        now = datetime.now(timezone.utc)
        status = "Submitted"
        if assignment.due_date:
            due_aware = assignment.due_date if assignment.due_date.tzinfo else assignment.due_date.replace(tzinfo=timezone.utc)
            if now > due_aware:
                status = "Late"

        if sub:
            sub.submission_text = submission_text
            sub.attachment_url = attachment_url or sub.attachment_url
            sub.submitted_at = now
            sub.status = status
        else:
            sub = AssignmentSubmission(
                assignment_id=assignment.id,
                student_id=student.id,
                submission_text=submission_text,
                attachment_url=attachment_url,
                submitted_at=now,
                status=status,
            )
            db.session.add(sub)

        db.session.commit()
        return sub

    @staticmethod
    def grade_submission(
        teacher: Teacher,
        submission_id: int,
        marks_obtained: float,
        feedback: Optional[str] = None,
    ) -> AssignmentSubmission:
        """Grade a student submission. Only the course teacher can grade."""
        sub = AssignmentSubmission.query.get_or_404(submission_id)
        if not teacher.teaches_subject(sub.assignment.subject_id):
            raise AuthorizationError("Teacher is not authorized to grade this assignment.")

        if marks_obtained < 0 or marks_obtained > sub.assignment.max_marks:
            raise ValidationError(f"Marks must be between 0 and {sub.assignment.max_marks}.")

        sub.marks_obtained = marks_obtained
        sub.feedback = feedback
        sub.graded_at = datetime.now(timezone.utc)
        sub.status = "Graded"
        db.session.commit()
        return sub

    # ── 3. Online Tests ────────────────────────────────────────────────────

    @staticmethod
    def create_test(
        teacher: Teacher,
        subject_id: int,
        title: str,
        description: str,
        duration_minutes: int,
        total_marks: float,
        passing_marks: float,
    ) -> Test:
        """Create an online test."""
        if not teacher.teaches_subject(subject_id):
            raise AuthorizationError("Teacher is not authorized to create tests for this subject.")

        test = Test(
            subject_id=subject_id,
            teacher_id=teacher.id,
            title=title,
            description=description,
            duration_minutes=duration_minutes,
            total_marks=total_marks,
            passing_marks=passing_marks,
            is_published=True,
        )
        db.session.add(test)
        db.session.commit()
        return test

    @staticmethod
    def add_question(
        teacher: Teacher,
        test_id: int,
        question_text: str,
        option_a: str,
        option_b: str,
        option_c: str,
        option_d: str,
        correct_option: str,
        marks: float = 1.0,
    ) -> Question:
        """Add MCQ question to test."""
        test = Test.query.get_or_404(test_id)
        if not teacher.teaches_subject(test.subject_id):
            raise AuthorizationError("Teacher is not authorized to edit this test.")

        order_idx = test.questions.count()
        q = Question(
            test_id=test.id,
            question_text=question_text,
            option_a=option_a,
            option_b=option_b,
            option_c=option_c,
            option_d=option_d,
            correct_option=correct_option.strip().upper(),
            marks=marks,
            order_index=order_idx,
        )
        db.session.add(q)
        db.session.commit()
        return q

    @staticmethod
    def start_test_attempt(student: Student, test_id: int) -> TestAttempt:
        """Student starts taking an online test."""
        test = Test.query.get_or_404(test_id)
        if not test.is_published:
            raise ValidationError("This test is not published yet.")

        # Check existing attempt
        attempt = TestAttempt.query.filter_by(test_id=test.id, student_id=student.id).first()
        if attempt:
            if attempt.status == "submitted":
                raise ValidationError("You have already submitted this test. Duplicate submissions are not allowed.")
            return attempt

        attempt = TestAttempt(
            test_id=test.id,
            student_id=student.id,
            started_at=datetime.now(timezone.utc),
            total_marks=test.total_marks,
            status="in_progress",
        )
        db.session.add(attempt)
        db.session.commit()
        return attempt

    @staticmethod
    def submit_test_attempt(
        student: Student,
        test_id: int,
        answers: Dict[int, str],
    ) -> TestAttempt:
        """
        Submit answers for an online test.
        Computes score immediately and prevents further edits.
        """
        attempt = TestAttempt.query.filter_by(test_id=test_id, student_id=student.id).first()
        if not attempt:
            raise ValidationError("Test attempt was not started.")

        if attempt.status == "submitted":
            raise ValidationError("Test has already been submitted.")

        test = attempt.test
        total_score = 0.0

        for q in test.questions.all():
            selected = answers.get(q.id, "").strip().upper()
            is_correct = (selected == q.correct_option.upper()) if selected else False
            marks_awarded = q.marks if is_correct else 0.0
            total_score += marks_awarded

            answer_record = TestAnswer(
                attempt_id=attempt.id,
                question_id=q.id,
                selected_option=selected or None,
                is_correct=is_correct,
                marks_awarded=marks_awarded,
            )
            db.session.add(answer_record)

        attempt.score = total_score
        attempt.submitted_at = datetime.now(timezone.utc)
        attempt.status = "submitted"
        db.session.commit()
        return attempt

    # ── 4. Fees ────────────────────────────────────────────────────────────

    @staticmethod
    def pay_fee(student: Student, fee_id: int) -> Fee:
        """Simulate paying a fee invoice."""
        fee = Fee.query.get_or_404(fee_id)
        if fee.student_id != student.id:
            raise AuthorizationError("Cannot pay another student's fee.")

        if fee.status == "Paid":
            return fee

        fee.amount_paid = fee.amount
        fee.status = "Paid"
        fee.paid_at = datetime.now(timezone.utc)
        fee.receipt_number = f"REC-{datetime.now().year}-{fee.id:04d}-{uuid.uuid4().hex[:6].upper()}"
        db.session.commit()
        return fee

    # ── 5. Feedback ────────────────────────────────────────────────────────

    @staticmethod
    def submit_feedback(
        user: User,
        feedback_type: str,
        category: str,
        rating: int,
        comments: str,
        teacher_id: Optional[int] = None,
        subject_id: Optional[int] = None,
        is_anonymous: bool = False,
    ) -> Feedback:
        """Submit role-appropriate feedback."""
        if rating < 1 or rating > 5:
            raise ValidationError("Rating must be between 1 and 5.")

        student_id = None
        if user.is_student:
            feedback_type = "student_to_teacher"
            student_id = user.student_profile.id if user.student_profile else None
        elif user.is_teacher:
            feedback_type = "teacher_to_management"

        fb = Feedback(
            feedback_type=feedback_type,
            user_id=user.id,
            student_id=student_id,
            teacher_id=teacher_id,
            subject_id=subject_id,
            category=category,
            rating=rating,
            comments=comments,
            is_anonymous=is_anonymous,
            status="Submitted",
        )
        db.session.add(fb)
        db.session.commit()
        return fb

    # ── 6. Announcements ───────────────────────────────────────────────────

    @staticmethod
    def create_announcement(
        user: User,
        title: str,
        content: str,
        category: str,
        target_role: str = "all",
        department_id: Optional[int] = None,
        is_pinned: bool = False,
    ) -> Announcement:
        """Create announcement."""
        valid_categories = ["College Management", "Teachers", "Student Coordinators"]
        if category not in valid_categories:
            category = "College Management"

        ann = Announcement(
            title=title,
            content=content,
            category=category,
            target_role=target_role,
            author_id=user.id,
            department_id=department_id,
            is_pinned=is_pinned,
        )
        db.session.add(ann)
        db.session.commit()
        return ann

    # ── 7. Lecture Replacement Requests ───────────────────────────────────

    @staticmethod
    def request_replacement(
        requester: Teacher,
        substitute_id: int,
        subject_id: int,
        req_date: date,
        time_slot: str,
        reason: str,
    ) -> LectureReplacementRequest:
        """Teacher requests a colleague to take a lecture."""
        if not requester.teaches_subject(subject_id):
            raise AuthorizationError("Requester does not teach this subject.")

        substitute = Teacher.query.get_or_404(substitute_id)
        if substitute.id == requester.id:
            raise ValidationError("Cannot request replacement from yourself.")

        req = LectureReplacementRequest(
            requester_id=requester.id,
            substitute_id=substitute.id,
            subject_id=subject_id,
            date=req_date,
            time_slot=time_slot,
            reason=reason,
            status="Pending",
        )
        db.session.add(req)
        db.session.commit()
        return req

    @staticmethod
    def respond_replacement(
        teacher: Teacher,
        request_id: int,
        accept: bool,
    ) -> LectureReplacementRequest:
        """Substitute teacher accepts or rejects the swap request."""
        req = LectureReplacementRequest.query.get_or_404(request_id)
        if req.substitute_id != teacher.id:
            raise AuthorizationError("Only the nominated substitute teacher can respond to this request.")

        req.status = "Approved" if accept else "Rejected"
        req.reviewed_at = datetime.now(timezone.utc)
        db.session.commit()
        return req
