"""
Campus_Sync – College Management API & Action Endpoints (Phase 4)
Handles CRUD operations for Attendance, Assignments, Tests, Fees, Feedback,
Announcements, and Lecture Replacements with strict role and resource checks.
"""

from datetime import datetime, date
from flask import Blueprint, request, jsonify, redirect, url_for, flash, abort
from flask_login import current_user

from app.auth.decorators import login_required, role_required
from app.services.college_service import CollegeService, AuthorizationError, ValidationError
from app.models.teacher import Teacher
from app.models.student import Student
from app.models.target import TeacherTarget
from app.database.db import db

college_api_bp = Blueprint("college_api", __name__, url_prefix="/api")


def _get_request_data():
    """Helper to read data whether sent as JSON or form data."""
    if request.is_json:
        return request.get_json() or {}
    return request.form.to_dict()


# ── 1. Attendance ──────────────────────────────────────────────────────────

@college_api_bp.route("/attendance/mark", methods=["POST"])
@login_required
@role_required("teacher")
def mark_attendance():
    """Teacher marks attendance for a class."""
    teacher = current_user.teacher_profile
    data = _get_request_data()

    subject_id = int(data.get("subject_id", 0))
    date_str = data.get("date")
    att_date = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else date.today()

    # Supports either list of records or single student form input
    records = data.get("records")
    if records is None:
        student_id = data.get("student_id")
        status = data.get("status", "Present")
        remarks = data.get("remarks")
        if student_id:
            records = [{"student_id": int(student_id), "status": status, "remarks": remarks}]
        else:
            records = []

    try:
        saved = CollegeService.mark_attendance(teacher, subject_id, att_date, records)
        if request.is_json:
            return jsonify({"status": "success", "count": len(saved)}), 200
        flash("Attendance recorded successfully.", "success")
        return redirect(url_for("dashboard.academics") + "#tab-attendance")
    except AuthorizationError as e:
        if request.is_json:
            return jsonify({"error": str(e)}), 403
        abort(403)
    except Exception as e:
        if request.is_json:
            return jsonify({"error": str(e)}), 400
        flash(f"Error marking attendance: {e}", "danger")
        return redirect(url_for("dashboard.academics"))


# ── 2. Assignments & Submissions ───────────────────────────────────────────

@college_api_bp.route("/assignments/create", methods=["POST"])
@login_required
@role_required("teacher")
def create_assignment():
    """Teacher creates an assignment."""
    teacher = current_user.teacher_profile
    data = _get_request_data()

    subject_id = int(data.get("subject_id", 0))
    title = data.get("title", "").strip()
    description = data.get("description", "").strip()
    due_date_str = data.get("due_date")
    max_marks = float(data.get("max_marks", 100))

    if not title or not due_date_str:
        if request.is_json:
            return jsonify({"error": "Title and due date are required."}), 400
        flash("Title and due date are required.", "danger")
        return redirect(url_for("dashboard.academics"))

    try:
        # Handle datetime-local "YYYY-MM-DDTHH:MM" or "YYYY-MM-DD"
        if "T" in due_date_str:
            due_date = datetime.strptime(due_date_str, "%Y-%m-%dT%H:%M")
        else:
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d")

        assign = CollegeService.create_assignment(
            teacher, subject_id, title, description, due_date, max_marks
        )
        if request.is_json:
            return jsonify({"status": "success", "assignment_id": assign.id}), 201
        flash("Assignment created successfully.", "success")
        return redirect(url_for("dashboard.academics") + "#tab-assignments")
    except AuthorizationError as e:
        if request.is_json:
            return jsonify({"error": str(e)}), 403
        abort(403)
    except Exception as e:
        if request.is_json:
            return jsonify({"error": str(e)}), 400
        flash(f"Error: {e}", "danger")
        return redirect(url_for("dashboard.academics"))


@college_api_bp.route("/assignments/<int:assignment_id>/submit", methods=["POST"])
@login_required
@role_required("student")
def submit_assignment(assignment_id: int):
    """Student submits coursework for an assignment."""
    student = current_user.student_profile
    data = _get_request_data()
    text = data.get("submission_text", "")
    url = data.get("attachment_url")

    try:
        sub = CollegeService.submit_assignment(student, assignment_id, text, url)
        if request.is_json:
            return jsonify({"status": "success", "submission_id": sub.id, "sub_status": sub.status}), 200
        flash("Assignment submitted successfully.", "success")
        return redirect(url_for("dashboard.academics") + "#tab-assignments")
    except Exception as e:
        if request.is_json:
            return jsonify({"error": str(e)}), 400
        flash(f"Submission error: {e}", "danger")
        return redirect(url_for("dashboard.academics"))


@college_api_bp.route("/assignments/submissions/<int:submission_id>/grade", methods=["POST"])
@login_required
@role_required("teacher")
def grade_submission(submission_id: int):
    """Teacher grades an assignment submission."""
    teacher = current_user.teacher_profile
    data = _get_request_data()

    try:
        marks = float(data.get("marks_obtained", 0))
        feedback = data.get("feedback")
        sub = CollegeService.grade_submission(teacher, submission_id, marks, feedback)
        if request.is_json:
            return jsonify({"status": "success", "submission_id": sub.id, "marks": marks}), 200
        flash("Grading saved successfully.", "success")
        return redirect(url_for("dashboard.academics") + "#tab-assignments")
    except AuthorizationError as e:
        if request.is_json:
            return jsonify({"error": str(e)}), 403
        abort(403)
    except ValidationError as e:
        if request.is_json:
            return jsonify({"error": str(e)}), 400
        flash(str(e), "danger")
        return redirect(url_for("dashboard.academics"))


# ── 3. Online Tests ────────────────────────────────────────────────────────

@college_api_bp.route("/tests/create", methods=["POST"])
@login_required
@role_required("teacher")
def create_test():
    """Teacher creates a new online test."""
    teacher = current_user.teacher_profile
    data = _get_request_data()

    try:
        subject_id = int(data.get("subject_id", 0))
        title = data.get("title", "").strip()
        description = data.get("description", "")
        duration = int(data.get("duration_minutes", 30))
        total_marks = float(data.get("total_marks", 20.0))
        passing_marks = float(data.get("passing_marks", 8.0))

        test = CollegeService.create_test(
            teacher, subject_id, title, description, duration, total_marks, passing_marks
        )
        if request.is_json:
            return jsonify({"status": "success", "test_id": test.id}), 201
        flash("Online test created.", "success")
        return redirect(url_for("dashboard.academics") + "#tab-tests")
    except AuthorizationError as e:
        if request.is_json:
            return jsonify({"error": str(e)}), 403
        abort(403)
    except Exception as e:
        if request.is_json:
            return jsonify({"error": str(e)}), 400
        flash(f"Error: {e}", "danger")
        return redirect(url_for("dashboard.academics"))


@college_api_bp.route("/tests/<int:test_id>/questions", methods=["POST"])
@login_required
@role_required("teacher")
def add_question(test_id: int):
    """Teacher adds an MCQ question to a test."""
    teacher = current_user.teacher_profile
    data = _get_request_data()

    try:
        q = CollegeService.add_question(
            teacher=teacher,
            test_id=test_id,
            question_text=data.get("question_text", ""),
            option_a=data.get("option_a", ""),
            option_b=data.get("option_b", ""),
            option_c=data.get("option_c", ""),
            option_d=data.get("option_d", ""),
            correct_option=data.get("correct_option", "A"),
            marks=float(data.get("marks", 1.0)),
        )
        if request.is_json:
            return jsonify({"status": "success", "question_id": q.id}), 201
        flash("Question added to test.", "success")
        return redirect(url_for("dashboard.academics") + "#tab-tests")
    except AuthorizationError as e:
        if request.is_json:
            return jsonify({"error": str(e)}), 403
        abort(403)
    except Exception as e:
        if request.is_json:
            return jsonify({"error": str(e)}), 400
        flash(f"Error: {e}", "danger")
        return redirect(url_for("dashboard.academics"))


@college_api_bp.route("/tests/<int:test_id>/start", methods=["POST"])
@login_required
@role_required("student")
def start_test(test_id: int):
    """Student starts a test session."""
    student = current_user.student_profile
    try:
        attempt = CollegeService.start_test_attempt(student, test_id)
        if request.is_json:
            return jsonify({"status": "success", "attempt_id": attempt.id, "test_id": test_id}), 200
        return redirect(url_for("dashboard.take_test", test_id=test_id))
    except ValidationError as e:
        if request.is_json:
            return jsonify({"error": str(e)}), 400
        flash(str(e), "warning")
        return redirect(url_for("dashboard.academics") + "#tab-tests")


@college_api_bp.route("/tests/<int:test_id>/submit", methods=["POST"])
@login_required
@role_required("student")
def submit_test(test_id: int):
    """Student submits answers for an online test."""
    student = current_user.student_profile
    data = _get_request_data()

    # Answers map: {question_id: selected_option}
    # In form submission, field names are like "question_12": "B"
    answers = {}
    if request.is_json and "answers" in data:
        raw_answers = data["answers"]
        for k, v in raw_answers.items():
            answers[int(k)] = str(v)
    else:
        for k, v in data.items():
            if k.startswith("q_") or k.startswith("question_"):
                qid = int(k.split("_")[1])
                answers[qid] = str(v)

    try:
        attempt = CollegeService.submit_test_attempt(student, test_id, answers)
        if request.is_json:
            return jsonify({
                "status": "success",
                "score": attempt.score,
                "total_marks": attempt.total_marks,
                "percentage": attempt.percentage,
            }), 200
        flash(f"Test submitted! Your score: {attempt.score} / {attempt.total_marks} ({attempt.percentage}%)", "success")
        return redirect(url_for("dashboard.academics") + "#tab-tests")
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400



# ── 4. Fees ────────────────────────────────────────────────────────────────

@college_api_bp.route("/fees/<int:fee_id>/pay", methods=["POST"])
@login_required
@role_required("student")
def pay_fee(fee_id: int):
    """Student pays a pending fee invoice."""
    student = current_user.student_profile
    try:
        fee = CollegeService.pay_fee(student, fee_id)
        if request.is_json:
            return jsonify({
                "status": "success",
                "receipt_number": fee.receipt_number,
                "paid_at": fee.paid_at.isoformat() if fee.paid_at else None,
            }), 200
        flash(f"Fee paid successfully! Receipt: {fee.receipt_number}", "success")
        return redirect(url_for("dashboard.exams") + "#tab-fees")
    except AuthorizationError as e:
        if request.is_json:
            return jsonify({"error": str(e)}), 403
        abort(403)


# ── 5. Feedback ────────────────────────────────────────────────────────────

@college_api_bp.route("/feedback/submit", methods=["POST"])
@login_required
def submit_feedback():
    """Submit student or teacher feedback."""
    data = _get_request_data()
    category = data.get("category", "General")
    rating = int(data.get("rating", 5))
    comments = data.get("comments", "").strip()
    is_anon = bool(data.get("is_anonymous"))
    teacher_id = int(data.get("teacher_id")) if data.get("teacher_id") else None
    subject_id = int(data.get("subject_id")) if data.get("subject_id") else None

    if not comments:
        if request.is_json:
            return jsonify({"error": "Comments are required."}), 400
        flash("Comments cannot be empty.", "danger")
        return redirect(url_for("dashboard.feedback"))

    try:
        fb = CollegeService.submit_feedback(
            user=current_user,
            feedback_type="student_to_teacher" if current_user.is_student else "teacher_to_management",
            category=category,
            rating=rating,
            comments=comments,
            teacher_id=teacher_id,
            subject_id=subject_id,
            is_anonymous=is_anon,
        )
        if request.is_json:
            return jsonify({"status": "success", "feedback_id": fb.id}), 201
        flash("Feedback submitted successfully. Thank you for your contribution!", "success")
        return redirect(url_for("dashboard.feedback"))
    except ValidationError as e:
        if request.is_json:
            return jsonify({"error": str(e)}), 400
        flash(str(e), "danger")
        return redirect(url_for("dashboard.feedback"))


# ── 6. Announcements ───────────────────────────────────────────────────────

@college_api_bp.route("/announcements/create", methods=["POST"])
@login_required
def create_announcement():
    """Create announcement by authorized users."""
    data = _get_request_data()
    title = data.get("title", "").strip()
    content = data.get("content", "").strip()
    category = data.get("category", "Teachers")
    target_role = data.get("target_role", "all")
    is_pinned = bool(data.get("is_pinned"))

    if not title or not content:
        if request.is_json:
            return jsonify({"error": "Title and content are required."}), 400
        flash("Title and content are required.", "danger")
        return redirect(url_for("dashboard.announcements"))

    ann = CollegeService.create_announcement(
        user=current_user,
        title=title,
        content=content,
        category=category,
        target_role=target_role,
        is_pinned=is_pinned,
    )
    if request.is_json:
        return jsonify({"status": "success", "announcement_id": ann.id}), 201
    flash("Announcement published successfully.", "success")
    return redirect(url_for("dashboard.announcements"))


# ── 7. Lecture Replacement Requests ───────────────────────────────────────

@college_api_bp.route("/replacement-requests/create", methods=["POST"])
@login_required
@role_required("teacher")
def create_replacement_request():
    """Teacher submits a lecture replacement request."""
    teacher = current_user.teacher_profile
    data = _get_request_data()

    substitute_id = int(data.get("substitute_id", 0))
    subject_id = int(data.get("subject_id", 0))
    date_str = data.get("date")
    time_slot = data.get("time_slot", "").strip()
    reason = data.get("reason", "").strip()

    if not date_str or not time_slot:
        if request.is_json:
            return jsonify({"error": "Date and time slot are required."}), 400
        flash("Date and time slot are required.", "danger")
        return redirect(url_for("dashboard.teacher_dashboard"))

    req_date = datetime.strptime(date_str, "%Y-%m-%d").date()

    try:
        req = CollegeService.request_replacement(
            requester=teacher,
            substitute_id=substitute_id,
            subject_id=subject_id,
            req_date=req_date,
            time_slot=time_slot,
            reason=reason,
        )
        if request.is_json:
            return jsonify({"status": "success", "request_id": req.id}), 201
        flash("Replacement request submitted to colleague.", "success")
        return redirect(url_for("dashboard.teacher_dashboard"))
    except AuthorizationError as e:
        if request.is_json:
            return jsonify({"error": str(e)}), 403
        abort(403)
    except ValidationError as e:
        if request.is_json:
            return jsonify({"error": str(e)}), 400
        flash(str(e), "danger")
        return redirect(url_for("dashboard.teacher_dashboard"))


@college_api_bp.route("/replacement-requests/<int:request_id>/respond", methods=["POST"])
@login_required
@role_required("teacher")
def respond_replacement_request(request_id: int):
    """Substitute teacher approves or rejects the request."""
    teacher = current_user.teacher_profile
    data = _get_request_data()
    action = data.get("action", "approve")  # "approve" or "reject"
    accept = action == "approve"

    try:
        req = CollegeService.respond_replacement(teacher, request_id, accept)
        if request.is_json:
            return jsonify({"status": "success", "request_status": req.status}), 200
        flash(f"Replacement request {req.status.lower()}.", "success")
        return redirect(url_for("dashboard.teacher_dashboard"))
    except AuthorizationError as e:
        if request.is_json:
            return jsonify({"error": str(e)}), 403
        abort(403)


# ── 8. Targets ─────────────────────────────────────────────────────────────

@college_api_bp.route("/targets/update", methods=["POST"])
@login_required
@role_required("teacher")
def update_target():
    """Teacher updates lecture count on syllabus delivery targets."""
    teacher = current_user.teacher_profile
    data = _get_request_data()

    target_id = int(data.get("target_id", 0))
    target = TeacherTarget.query.get_or_404(target_id)
    if target.teacher_id != teacher.id:
        if request.is_json:
            return jsonify({"error": "Unauthorized"}), 403
        abort(403)

    completed = int(data.get("completed_lectures", target.completed_lectures))
    target.completed_lectures = completed
    if target.completed_lectures >= target.planned_lectures:
        target.status = "Completed"
    db.session.commit()

    if request.is_json:
        return jsonify({"status": "success", "progress": target.progress_percentage}), 200
    flash("Target progress updated.", "success")
    return redirect(url_for("dashboard.academics") + "#tab-targets")
