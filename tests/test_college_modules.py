"""
Phase 4 – Database Models, Complete College Modules, Authorization & Security Tests
"""

from datetime import datetime, timezone, date, timedelta
import pytest
from app import create_app
from app.database.db import db as _db
from app.services.seeder import seed_all
from app.models import (
    User, Role, Student, Teacher, Subject, Department,
    Attendance, Assignment, AssignmentSubmission,
    Fee, Announcement, Syllabus, TeacherTarget,
    Test, Question, TestAttempt, TestAnswer,
    ExamTimetable, Result, Feedback, LectureReplacementRequest
)
from app.services.college_service import CollegeService, AuthorizationError, ValidationError


@pytest.fixture(scope="function")
def app():
    """Create testing app with in-memory SQLite and full demo seed data."""
    app = create_app("testing")
    with app.app_context():
        _db.create_all()
        seed_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def login_as(client, email, password):
    client.get("/logout", follow_redirects=True)
    return client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=True,
    )



# ── 1. Database Model Integrity & Aggregations ─────────────────────────────

def test_student_dashboard_live_aggregations(app):
    with app.app_context():
        stu = Student.query.filter_by(student_id="STU-2024-001").first()
        assert stu is not None
        assert stu.attendance_percentage > 0.0
        assert stu.total_lectures > 0
        assert stu.present_lectures > 0
        assert stu.pending_fees_amount == 350.0  # Lab fee pending in seed data


def test_teacher_dashboard_live_aggregations(app):
    with app.app_context():
        tch = Teacher.query.filter_by(teacher_id="TCH-2024-001").first()
        assert tch is not None
        assert tch.teaches_subject(Subject.query.filter_by(code="CS301").first().id) is True
        assert tch.teaches_subject(Subject.query.filter_by(code="CS201").first().id) is False
        assert tch.overall_target_progress > 0.0
        assert tch.pending_grading_count >= 1  # Student 2 submitted Assignment 1


# ── 2. Data Isolation & Security (Prevent ID Tampering) ─────────────────────

def test_student_cannot_access_other_student_profile(client):
    login_as(client, "student@test.com", "Student@123")
    # Student 1 owns STU-2024-001. Trying to access STU-2024-015 (Riya Sen)
    resp = client.get("/student/profile/STU-2024-015")
    assert resp.status_code == 403


def test_student_can_access_own_profile(client):
    login_as(client, "student@test.com", "Student@123")
    resp = client.get("/student/profile/STU-2024-001")
    assert resp.status_code == 200


def test_student_cannot_pay_other_student_fee(client, app):
    login_as(client, "student@test.com", "Student@123")
    with app.app_context():
        stu2 = Student.query.filter_by(student_id="STU-2024-015").first()
        fee_other = Fee(
            student_id=stu2.id,
            title="Other Student Dues",
            fee_type="Tuition",
            amount=500.0,
            due_date=date.today(),
            status="Pending",
        )
        _db.session.add(fee_other)
        _db.session.commit()
        fee_id = fee_other.id

    # Student 1 attempts to pay Student 2's fee
    resp = client.post(f"/api/fees/{fee_id}/pay", follow_redirects=False)
    assert resp.status_code == 403


# ── 3. Teacher Scoping & Authorization ─────────────────────────────────────

def test_teacher_cannot_create_assignment_for_unauthorized_subject(client, app):
    login_as(client, "teacher@test.com", "Teacher@123")  # Dr. Priya teaches CS301 & CS401, NOT CS201
    with app.app_context():
        cs201 = Subject.query.filter_by(code="CS201").first()
        subj_id = cs201.id

    resp = client.post(
        "/api/assignments/create",
        data={
            "subject_id": subj_id,
            "title": "Unauthorized Assignment",
            "due_date": "2026-10-25T10:00",
            "max_marks": 50,
        },
        follow_redirects=False,
    )
    assert resp.status_code == 403


def test_teacher_cannot_mark_attendance_for_unauthorized_subject(client, app):
    login_as(client, "teacher@test.com", "Teacher@123")
    with app.app_context():
        cs201 = Subject.query.filter_by(code="CS201").first()
        subj_id = cs201.id
        stu1 = Student.query.filter_by(student_id="STU-2024-001").first()
        stu_id = stu1.id

    resp = client.post(
        "/api/attendance/mark",
        data={
            "subject_id": subj_id,
            "date": "2026-10-06",
            "student_id": stu_id,
            "status": "Present",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 403


# ── 4. Online Test Lifecycle & Anti-Cheat Constraints ───────────────────────

def test_online_test_taking_and_instant_scoring(client, app):
    login_as(client, "student@test.com", "Student@123")
    with app.app_context():
        # Test 2 is unattempted by Student 1
        test2 = Test.query.filter_by(title="SQL Indexing & Query Plans Practice Quiz").first()
        t2_id = test2.id
        q_list = test2.questions.order_by(Question.order_index).all()
        # Answers: Q1 -> B (correct), Q2 -> A (correct), Q3 -> A (correct)
        answers = {f"question_{q.id}": q.correct_option for q in q_list}

    # Start test
    start_resp = client.post(f"/api/tests/{t2_id}/start", follow_redirects=True)
    assert start_resp.status_code == 200

    # Submit answers
    submit_resp = client.post(f"/api/tests/{t2_id}/submit", data=answers, follow_redirects=True)
    assert submit_resp.status_code == 200

    # Verify score in DB
    with app.app_context():
        stu = Student.query.filter_by(student_id="STU-2024-001").first()
        att = TestAttempt.query.filter_by(test_id=t2_id, student_id=stu.id).first()
        assert att.status == "submitted"
        assert att.score == 3.0
        assert att.total_marks == 3.0


def test_student_cannot_double_submit_test(client, app):
    login_as(client, "student@test.com", "Student@123")
    with app.app_context():
        # Test 1 is already completed by Student 1 in seed data
        test1 = Test.query.filter_by(title="Mid-Semester DBMS Quiz").first()
        t1_id = test1.id

    # Trying to submit again must fail
    resp = client.post(
        f"/api/tests/{t1_id}/submit",
        data={"question_1": "A"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 400


# ── 5. Feedback Workflow ───────────────────────────────────────────────────

def test_student_feedback_submission(client, app):
    login_as(client, "student@test.com", "Student@123")
    with app.app_context():
        tch = Teacher.query.filter_by(teacher_id="TCH-2024-001").first()
        subj = Subject.query.filter_by(code="CS301").first()
        tch_id, subj_id = tch.id, subj.id

    resp = client.post(
        "/api/feedback/submit",
        data={
            "teacher_id": tch_id,
            "subject_id": subj_id,
            "category": "Course Pacing",
            "rating": 5,
            "comments": "Great interactive problem sets and examples.",
            "is_anonymous": "1",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200


def test_teacher_management_feedback_submission(client):
    login_as(client, "teacher@test.com", "Teacher@123")
    resp = client.post(
        "/api/feedback/submit",
        data={
            "category": "Curriculum & Syllabus Revisions",
            "rating": 4,
            "comments": "Propose introducing Cloud Native tools to Semester 6 curriculum.",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200


# ── 6. Lecture Replacement Coordination ────────────────────────────────────

def test_lecture_replacement_request_and_response(client, app):
    # Teacher 1 requests replacement from Teacher 2
    login_as(client, "teacher@test.com", "Teacher@123")
    with app.app_context():
        tch2 = Teacher.query.filter_by(teacher_id="TCH-2024-002").first()
        cs301 = Subject.query.filter_by(code="CS301").first()
        tch2_id, cs301_id = tch2.id, cs301.id

    create_resp = client.post(
        "/api/replacement-requests/create",
        data={
            "substitute_id": tch2_id,
            "subject_id": cs301_id,
            "date": "2026-10-18",
            "time_slot": "09:00 AM - 10:00 AM",
            "reason": "Department research committee meeting.",
        },
        follow_redirects=True,
    )
    assert create_resp.status_code == 200

    # Teacher 2 logs in and accepts the request
    login_as(client, "teacher2@test.com", "Teacher@123")
    with app.app_context():
        req = LectureReplacementRequest.query.filter_by(
            reason="Department research committee meeting."
        ).first()
        req_id = req.id

    resp_action = client.post(
        f"/api/replacement-requests/{req_id}/respond",
        data={"action": "approve"},
        follow_redirects=True,
    )
    assert resp_action.status_code == 200

    with app.app_context():
        verified_req = LectureReplacementRequest.query.get(req_id)
        assert verified_req.status == "Approved"


# ── 7. Fee Payment Flow ────────────────────────────────────────────────────

def test_student_fee_payment_generates_receipt(client, app):
    login_as(client, "student@test.com", "Student@123")
    with app.app_context():
        stu = Student.query.filter_by(student_id="STU-2024-001").first()
        pending_fee = stu.fees.filter_by(status="Pending").first()
        fee_id = pending_fee.id

    resp = client.post(f"/api/fees/{fee_id}/pay", follow_redirects=True)
    assert resp.status_code == 200

    with app.app_context():
        fee = Fee.query.get(fee_id)
        assert fee.status == "Paid"
        assert fee.receipt_number is not None
        assert fee.receipt_number.startswith("REC-")


# ── 8. Module Views Render 200 with Real Data ──────────────────────────────

@pytest.mark.parametrize("route", [
    "/student",
    "/copilot",
    "/announcements",
    "/academics",
    "/exams",
    "/feedback",
    "/settings",
    "/profile",
])
def test_student_authenticated_modules_load(client, route):
    login_as(client, "student@test.com", "Student@123")
    resp = client.get(route)
    assert resp.status_code == 200


@pytest.mark.parametrize("route", [
    "/teacher",
    "/copilot",
    "/announcements",
    "/academics",
    "/exams",
    "/feedback",
    "/settings",
    "/profile",
])
def test_teacher_authenticated_modules_load(client, route):
    login_as(client, "teacher@test.com", "Teacher@123")
    resp = client.get(route)
    assert resp.status_code == 200
