"""
Phase 2 – Authentication & Role System Test Suite
Tests:
  - Student login
  - Teacher login
  - Wrong password
  - Logout
  - Unauthenticated access
  - Student -> teacher route
  - Teacher -> student route
  - Direct URL access
"""

import pytest
from app import create_app
from app.database.db import db as _db
from app.services.seeder import seed_all
from app.models.user import User, Role
from app.models.student import Student
from app.models.department import Department


@pytest.fixture(scope="function")
def app():
    """Create a testing app with in-memory DB and demo seed data."""
    app = create_app("testing")
    with app.app_context():
        _db.create_all()
        seed_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def fresh_client(app):
    """Provide a fresh, clean test client for every test."""
    return app.test_client()


def login_user(client, email, password):
    """Helper to perform login request."""
    return client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=False,
    )


# ── 1. Student Login ────────────────────────────────────────────────────────

def test_student_login(fresh_client):
    """Student logs in and gets redirected to /student."""
    resp = login_user(fresh_client, "student@test.com", "Student@123")
    assert resp.status_code == 302
    assert "/student" in resp.headers["Location"]

    # Follow redirect to student dashboard
    dashboard_resp = fresh_client.get(resp.headers["Location"])
    assert dashboard_resp.status_code == 200
    assert b"Student" in dashboard_resp.data
    assert b"Alex Johnson" in dashboard_resp.data


# ── 2. Teacher Login ────────────────────────────────────────────────────────

def test_teacher_login(fresh_client):
    """Teacher logs in and gets redirected to /teacher."""
    resp = login_user(fresh_client, "teacher@test.com", "Teacher@123")
    assert resp.status_code == 302
    assert "/teacher" in resp.headers["Location"]

    # Follow redirect to teacher dashboard
    dashboard_resp = fresh_client.get(resp.headers["Location"])
    assert dashboard_resp.status_code == 200
    assert b"Teacher" in dashboard_resp.data
    assert b"Dr. Priya Sharma" in dashboard_resp.data


# ── 3. Wrong Password ───────────────────────────────────────────────────────

def test_wrong_password(fresh_client):
    """Login with wrong password fails with 401."""
    resp = fresh_client.post(
        "/login",
        data={"email": "student@test.com", "password": "WrongPassword!"},
    )
    assert resp.status_code == 401
    assert b"Invalid email or password" in resp.data


def test_nonexistent_email(fresh_client):
    """Login with unknown email fails with 401."""
    resp = fresh_client.post(
        "/login",
        data={"email": "nonexistent@test.com", "password": "AnyPassword123"},
    )
    assert resp.status_code == 401
    assert b"Invalid email or password" in resp.data


# ── 4. Logout ───────────────────────────────────────────────────────────────

def test_logout(fresh_client):
    """Logging out terminates the session and prevents access to protected routes."""
    # Log in first
    login_user(fresh_client, "student@test.com", "Student@123")
    assert fresh_client.get("/student").status_code == 200

    # Log out
    logout_resp = fresh_client.get("/logout", follow_redirects=False)
    assert logout_resp.status_code == 302
    assert "/login" in logout_resp.headers["Location"]

    # Accessing /student again should redirect to login
    protected_resp = fresh_client.get("/student", follow_redirects=False)
    assert protected_resp.status_code == 302
    assert "/login" in protected_resp.headers["Location"]


# ── 5. Unauthenticated Access ───────────────────────────────────────────────

def test_unauthenticated_student_route(fresh_client):
    """Unauthenticated access to /student redirects to /login."""
    resp = fresh_client.get("/student", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_unauthenticated_teacher_route(fresh_client):
    """Unauthenticated access to /teacher redirects to /login."""
    resp = fresh_client.get("/teacher", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_unauthenticated_dashboard_route(fresh_client):
    """Unauthenticated access to /dashboard redirects to /login."""
    resp = fresh_client.get("/dashboard", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


# ── 6. Student → Teacher Route (Role-Based Restriction) ─────────────────────

def test_student_cannot_access_teacher_route(fresh_client):
    """Authenticated student attempting to access /teacher must receive 403 Forbidden."""
    login_user(fresh_client, "student@test.com", "Student@123")
    resp = fresh_client.get("/teacher", follow_redirects=False)
    assert resp.status_code == 403
    assert b"403" in resp.data
    assert b"Access Denied" in resp.data


# ── 7. Teacher → Student Route (Role-Based Restriction) ─────────────────────

def test_teacher_cannot_access_student_route(fresh_client):
    """Authenticated teacher attempting to access /student must receive 403 Forbidden."""
    login_user(fresh_client, "teacher@test.com", "Teacher@123")
    resp = fresh_client.get("/student", follow_redirects=False)
    assert resp.status_code == 403
    assert b"403" in resp.data
    assert b"Access Denied" in resp.data


# ── 8. Direct URL Access & Ownership ───────────────────────────────────────

def test_student_can_access_own_profile(fresh_client):
    """Student can access their own profile URL directly."""
    login_user(fresh_client, "student@test.com", "Student@123")
    resp = fresh_client.get("/student/profile/STU-2024-001")
    assert resp.status_code == 200
    assert b"Alex Johnson" in resp.data


def test_student_cannot_access_other_student_profile(app, fresh_client):
    """Student A cannot access Student B's profile by changing the URL."""
    with app.app_context():
        dept = Department.query.filter_by(code="CS").first()
        u2 = User.query.filter_by(email="student2@test.com").first()
        if not u2:
            u2 = User(email="student2@test.com", role=Role.STUDENT)
            u2.set_password("Student2@123")
            _db.session.add(u2)
            _db.session.flush()
            s2 = Student(
                student_id="STU-2024-999",
                user_id=u2.id,
                name="Other Student",
                department_id=dept.id,
                semester=1,
            )
            _db.session.add(s2)
            _db.session.commit()

    # Log in as original student
    login_user(fresh_client, "student@test.com", "Student@123")
    # Try to access student 2's profile
    resp = fresh_client.get("/student/profile/STU-2024-999")
    assert resp.status_code == 403


def test_student_cannot_access_teacher_profile(fresh_client):
    """Student cannot access teacher profile directly."""
    login_user(fresh_client, "student@test.com", "Student@123")
    resp = fresh_client.get("/teacher/profile/TCH-2024-001")
    assert resp.status_code == 403
