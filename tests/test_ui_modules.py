"""
Phase 3 – Complete UI System, Navigation, and Module Tests
"""

import pytest
from app import create_app
from app.database.db import db as _db
from app.services.seeder import seed_all


@pytest.fixture(scope="function")
def app():
    """Create testing app with in-memory DB and demo seed data."""
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
    return client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=True,
    )


# ── 1. Unauthenticated Protection on all Phase 3 Module Routes ─────────────

@pytest.mark.parametrize("route", [
    "/copilot",
    "/announcements",
    "/academics",
    "/exams",
    "/feedback",
    "/settings",
    "/profile",
])
def test_unauthenticated_modules_redirect_to_login(client, route):
    resp = client.get(route, follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


# ── 2. Authenticated Student Navigation ───────────────────────────────────

def test_student_can_access_all_modules(client):
    login_as(client, "student@test.com", "Student@123")
    for route in ["/copilot", "/announcements", "/academics", "/exams", "/feedback", "/settings", "/profile"]:
        resp = client.get(route)
        assert resp.status_code == 200, f"Failed on {route}"


def test_student_dashboard_has_student_specific_content(client):
    resp = login_as(client, "student@test.com", "Student@123")
    assert resp.status_code == 200
    # Must have Copilot section
    assert b"AI College Copilot" in resp.data
    # Must have Student cards
    assert b"Profile" in resp.data
    assert b"Attendance" in resp.data
    assert b"Assignments" in resp.data
    assert b"Fees" in resp.data
    # Must NOT have Teacher-only cards
    assert b"Lecture Replacement Request" not in resp.data
    assert b"Paper Checking" not in resp.data


# ── 3. Authenticated Teacher Navigation ───────────────────────────────────

def test_teacher_can_access_all_modules(client):
    login_as(client, "teacher@test.com", "Teacher@123")
    for route in ["/copilot", "/announcements", "/academics", "/exams", "/feedback", "/settings", "/profile"]:
        resp = client.get(route)
        assert resp.status_code == 200, f"Failed on {route}"


def test_teacher_dashboard_has_teacher_specific_content(client):
    resp = login_as(client, "teacher@test.com", "Teacher@123")
    assert resp.status_code == 200
    # Must have Copilot section
    assert b"AI College Copilot" in resp.data
    # Must have Teacher cards
    assert b"Profile" in resp.data
    assert b"Target" in resp.data
    assert b"Checking" in resp.data
    assert b"Lecture Replacement Request" in resp.data
    # Must NOT have Student-only cards
    assert b"Assignments" not in resp.data
    assert b"Check Attendance" not in resp.data
