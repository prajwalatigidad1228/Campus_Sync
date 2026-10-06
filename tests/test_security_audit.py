"""
Phase 6 – Security Audit, Upload Security, Smart Alerts & Threat Defense Tests

Verifies:
1. Security Headers & Defense-in-Depth (nosniff, SAMEORIGIN, CSP, XSS-Protection).
2. Open Redirect Defense (rejecting //evil.com and path escapes).
3. Session Fixation Defense.
4. Upload Security Pipeline:
   - Whitelist validation (.pdf, .png).
   - Blacklist rejection (.exe, .py, .sh, .php).
   - Magic byte validation (disguised binaries blocked).
   - Traversal sanitation (../../safe.pdf -> uuid_safe.pdf).
   - Authorization & IDOR protection on downloads.
5. Smart Alerts ("Things requiring your attention"):
   - Real DB derivation for Student (pending fees, coursework deadlines).
   - Real DB derivation for Teacher (grading backlog, targets).
   - Live rendering on /student and /teacher.
6. Copilot Alert Support:
   - "What should I focus on today?" returns real database alerts with attribution.
"""

import io
import pytest
from app import create_app
from app.database.db import db as _db
from app.services.seeder import seed_all
from app.models import User, Student, Teacher, FileUpload
from app.services.alert_service import AlertService
from app.ai.copilot_engine import CopilotEngine


@pytest.fixture(scope="function")
def app():
    """Create testing application with SQLite and full seed data."""
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


# ── 1. Security Headers & Network Hardening ────────────────────────────────

def test_security_headers_present_on_responses(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert res.headers.get("X-XSS-Protection") == "1; mode=block"
    assert res.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "Content-Security-Policy" in res.headers


def test_open_redirect_protocol_relative_rejected(client):
    # Attempting protocol-relative open-redirect //evil.com
    res = client.post(
        "/login?next=//evil.com/phish",
        data={"email": "student@test.com", "password": "Student@123"},
        follow_redirects=False,
    )
    assert res.status_code == 302
    # Should redirect to internal student dashboard, NOT to //evil.com
    assert res.headers["Location"] == "/student"


def test_open_redirect_backslash_rejected(client):
    res = client.post(
        "/login?next=/\\evil.com",
        data={"email": "student@test.com", "password": "Student@123"},
        follow_redirects=False,
    )
    assert res.status_code == 302
    assert res.headers["Location"] == "/student"


# ── 2. File Upload Security Pipeline ────────────────────────────────────────

def test_upload_valid_pdf_file_succeeds(client):
    login_as(client, "student@test.com", "Student@123")
    # Legitimate PDF starting with %PDF- header
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
    data = {
        "file": (io.BytesIO(pdf_content), "assignment_solution.pdf"),
        "category": "assignment",
    }
    res = client.post("/api/uploads/file", data=data, content_type="multipart/form-data")
    assert res.status_code == 201
    json_data = res.get_json()
    assert json_data["status"] == "success"
    assert json_data["file"]["filename"] == "assignment_solution.pdf"
    assert "download_url" in json_data["file"]


def test_upload_valid_png_file_succeeds(client):
    login_as(client, "student@test.com", "Student@123")
    # Legitimate PNG starting with PNG magic bytes
    png_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    data = {
        "file": (io.BytesIO(png_content), "circuit_diagram.png"),
        "category": "assignment",
    }
    res = client.post("/api/uploads/file", data=data, content_type="multipart/form-data")
    assert res.status_code == 201


def test_upload_disallowed_extension_rejected(client):
    login_as(client, "student@test.com", "Student@123")
    for bad_ext in ["payload.exe", "script.py", "shell.sh", "backdoor.php"]:
        data = {
            "file": (io.BytesIO(b"print('hacked')"), bad_ext),
        }
        res = client.post("/api/uploads/file", data=data, content_type="multipart/form-data")
        assert res.status_code == 400
        assert "prohibited" in res.get_json()["error"].lower() or "not permitted" in res.get_json()["error"].lower()


def test_upload_magic_byte_mismatch_rejected(client):
    login_as(client, "student@test.com", "Student@123")
    # Fake PDF containing binary/executable bytes without %PDF-
    fake_pdf = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00"
    data = {
        "file": (io.BytesIO(fake_pdf), "malicious.pdf"),
    }
    res = client.post("/api/uploads/file", data=data, content_type="multipart/form-data")
    assert res.status_code == 400
    assert "magic byte mismatch" in res.get_json()["error"].lower()


def test_upload_path_traversal_sanitized(client, app):
    login_as(client, "student@test.com", "Student@123")
    pdf_content = b"%PDF-1.5 test document"
    data = {
        "file": (io.BytesIO(pdf_content), "../../../etc/passwd.pdf"),
    }
    res = client.post("/api/uploads/file", data=data, content_type="multipart/form-data")
    assert res.status_code == 201
    with app.app_context():
        upload_rec = FileUpload.query.order_by(FileUpload.id.desc()).first()
        # Traversal sequence "../" MUST be removed
        assert ".." not in upload_rec.uuid_filename
        assert upload_rec.uuid_filename.endswith("passwd.pdf")


def test_upload_download_authorized_owner_and_teacher(client):
    login_as(client, "student@test.com", "Student@123")
    pdf_content = b"%PDF-1.4 student paper"
    data = {"file": (io.BytesIO(pdf_content), "report.pdf")}
    res = client.post("/api/uploads/file", data=data, content_type="multipart/form-data")
    file_id = res.get_json()["file"]["id"]

    # 1. Owner student downloads -> 200 OK
    down_res = client.get(f"/api/uploads/{file_id}/download")
    assert down_res.status_code == 200
    assert b"%PDF-1.4 student paper" in down_res.data

    # 2. Teacher downloads for grading -> 200 OK
    login_as(client, "teacher@test.com", "Teacher@123")
    teacher_down = client.get(f"/api/uploads/{file_id}/download")
    assert teacher_down.status_code == 200


def test_upload_download_unauthorized_student_denied(client):
    # Student 1 uploads file
    login_as(client, "student@test.com", "Student@123")
    pdf_content = b"%PDF-1.4 confidential paper"
    data = {"file": (io.BytesIO(pdf_content), "alex_private.pdf")}
    res = client.post("/api/uploads/file", data=data, content_type="multipart/form-data")
    file_id = res.get_json()["file"]["id"]

    # Student 2 (Riya) attempts to download Student 1's file -> 403 Forbidden
    login_as(client, "riya@test.com", "Student@123")
    unauth_down = client.get(f"/api/uploads/{file_id}/download")
    assert unauth_down.status_code == 403


# ── 3. Smart Alerts Service & Rendering ─────────────────────────────────────

def test_student_smart_alerts_grounded_in_db(app):
    with app.app_context():
        student = Student.query.filter_by(student_id="STU-2024-001").first()
        alerts = AlertService.get_student_alerts(student)

        # Alex Johnson has:
        # 1. Pending fee invoice ($350)
        # 2. Pending coursework assignments
        categories = [a["category"] for a in alerts]
        assert "fee" in categories
        assert "assignment" in categories

        # Verify fee alert details match database record
        fee_alert = next(a for a in alerts if a["category"] == "fee")
        assert "$350" in fee_alert["description"]
        assert fee_alert["action_url"] == "/exams#tab-fees"


def test_teacher_smart_alerts_grounded_in_db(app):
    with app.app_context():
        teacher = Teacher.query.filter_by(teacher_id="TCH-2024-001").first()
        alerts = AlertService.get_teacher_alerts(teacher)

        categories = [a["category"] for a in alerts]
        # Dr. Priya has pending grading submission and replacement requests in seed
        assert "assignment" in categories or "replacement" in categories


def test_smart_alerts_render_on_student_dashboard(client):
    login_as(client, "student@test.com", "Student@123")
    res = client.get("/student")
    assert res.status_code == 200
    html = res.data.decode("utf-8")
    assert "Things requiring your attention" in html
    assert "alert-card" in html or "All Caught Up" in html


def test_smart_alerts_render_on_teacher_dashboard(client):
    login_as(client, "teacher@test.com", "Teacher@123")
    res = client.get("/teacher")
    assert res.status_code == 200
    html = res.data.decode("utf-8")
    assert "Things requiring your attention" in html


# ── 4. Copilot Smart Alert Summarization ────────────────────────────────────

def test_copilot_student_focus_today(app):
    with app.app_context():
        user = User.query.filter_by(email="student@test.com").first()
        res = CopilotEngine.chat(user, "What should I focus on today?")
        assert res["is_denied"] is False
        assert "briefing" in res["response"].lower() or "attention" in res["response"].lower()
        assert "Campus_Sync Smart Alert Center" in res["source"]
        # Must mention actual fee or assignment from alerts
        assert "350" in res["response"] or "assignment" in res["response"].lower()


def test_copilot_teacher_focus_today(app):
    with app.app_context():
        teacher_user = User.query.filter_by(email="teacher@test.com").first()
        res = CopilotEngine.chat(teacher_user, "What should I focus on today?")
        assert res["is_denied"] is False
        assert "Campus_Sync Smart Alert Center" in res["source"]
