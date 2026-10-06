"""
Campus_Sync – Dashboard & Navigation Routes (Phase 4)
Dynamic data binding, strict authorization checks, and student/teacher scoping.
"""

from datetime import datetime, timezone
from flask import Blueprint, render_template, abort, redirect, url_for, flash
from flask_login import current_user

from app.auth.decorators import (
    login_required,
    role_required,
    owns_student_profile,
    owns_teacher_profile,
)
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

dashboard_bp = Blueprint("dashboard", __name__)


# ── Primary Role Dashboards ────────────────────────────────────────────────

@dashboard_bp.route("/student")
@login_required
@role_required("student")
def student_dashboard():
    """Protected student dashboard route with live database metrics."""
    profile = current_user.student_profile

    # Real Attendance stats
    attendance_pct = profile.attendance_percentage if profile else 0.0
    total_lectures = profile.total_lectures if profile else 0
    present_lectures = profile.present_lectures if profile else 0
    absent_lectures = profile.absent_lectures if profile else 0

    # Real Assignments count
    dept_subj_ids = [s.id for s in profile.department.subjects] if profile and profile.department else []
    active_assignments = (
        Assignment.query.filter(Assignment.subject_id.in_(dept_subj_ids)).all()
        if dept_subj_ids
        else []
    )
    submitted_ids = (
        {s.assignment_id for s in profile.assignment_submissions.all()} if profile else set()
    )
    pending_assignments = [a for a in active_assignments if a.id not in submitted_ids]
    pending_assignments_count = len(pending_assignments)

    # Real Fees status
    pending_fees_amount = profile.pending_fees_amount if profile else 0.0
    fees_status = "Paid" if pending_fees_amount == 0 else f"${pending_fees_amount:,.0f} Pending"

    # Announcements for students
    announcements_list = (
        Announcement.query.filter(Announcement.target_role.in_(["all", "student"]))
        .order_by(Announcement.is_pinned.desc(), Announcement.created_at.desc())
        .limit(5)
        .all()
    )

    # Real Smart Alerts (Things requiring your attention)
    from app.services.alert_service import AlertService
    alerts = AlertService.get_student_alerts(profile) if profile else []

    return render_template(
        "dashboard/student.html",
        profile=profile,
        attendance_pct=attendance_pct,
        total_lectures=total_lectures,
        present_lectures=present_lectures,
        absent_lectures=absent_lectures,
        pending_assignments_count=pending_assignments_count,
        pending_fees_amount=pending_fees_amount,
        fees_status=fees_status,
        announcements=announcements_list,
        alerts=alerts,
    )


@dashboard_bp.route("/teacher")
@login_required
@role_required("teacher")
def teacher_dashboard():
    """Protected teacher dashboard route with live database metrics."""
    profile = current_user.teacher_profile

    targets = profile.targets.all() if profile else []
    overall_target = profile.overall_target_progress if profile else 0.0
    pending_checking_count = profile.pending_grading_count if profile else 0
    pending_replacements_count = profile.pending_replacement_requests_count if profile else 0

    incoming_replacements = (
        profile.received_replacements.filter_by(status="Pending").all() if profile else []
    )
    sent_replacements = (
        profile.sent_replacements.order_by(LectureReplacementRequest.created_at.desc()).limit(5).all()
        if profile
        else []
    )
    colleagues = Teacher.query.filter(Teacher.id != profile.id).all() if profile else []

    announcements_list = (
        Announcement.query.filter(Announcement.target_role.in_(["all", "teacher"]))
        .order_by(Announcement.is_pinned.desc(), Announcement.created_at.desc())
        .limit(5)
        .all()
    )

    # Real Smart Alerts (Things requiring your attention)
    from app.services.alert_service import AlertService
    alerts = AlertService.get_teacher_alerts(profile) if profile else []

    return render_template(
        "dashboard/teacher.html",
        profile=profile,
        targets=targets,
        overall_target=overall_target,
        pending_checking_count=pending_checking_count,
        pending_replacements_count=pending_replacements_count,
        incoming_replacements=incoming_replacements,
        sent_replacements=sent_replacements,
        colleagues=colleagues,
        announcements=announcements_list,
        alerts=alerts,
    )



@dashboard_bp.route("/dashboard")
@login_required
def index():
    """Detect authenticated role and redirect to /student or /teacher."""
    if current_user.is_student:
        return redirect(url_for("dashboard.student_dashboard"))
    if current_user.is_teacher:
        return redirect(url_for("dashboard.teacher_dashboard"))
    abort(403)


# ── Module Pages (Phase 4 Real Data) ───────────────────────────────────────

@dashboard_bp.route("/copilot")
@login_required
def copilot():
    """AI College Copilot dedicated workspace."""
    return render_template("modules/copilot.html")


@dashboard_bp.route("/announcements")
@login_required
def announcements():
    """Announcements module (College Management, Teachers, Student Coordinators)."""
    target_roles = ["all", "student"] if current_user.is_student else ["all", "teacher"]
    announcements_list = (
        Announcement.query.filter(Announcement.target_role.in_(target_roles))
        .order_by(Announcement.is_pinned.desc(), Announcement.created_at.desc())
        .all()
    )
    return render_template("modules/announcements.html", announcements=announcements_list)


@dashboard_bp.route("/academics")
@login_required
def academics():
    """Academics module: Syllabus, Attendance, Assignments, Online Tests."""
    if current_user.is_student:
        student = current_user.student_profile
        subjects = (
            Subject.query.filter_by(
                department_id=student.department_id, semester=student.semester
            ).all()
            if student
            else []
        )
        if not subjects and student and student.department:
            subjects = student.department.subjects.all()

        subj_ids = [s.id for s in subjects]
        syllabi = (
            Syllabus.query.filter(Syllabus.subject_id.in_(subj_ids))
            .order_by(Syllabus.unit_number)
            .all()
            if subj_ids
            else []
        )
        attendances = (
            student.attendances.order_by(Attendance.date.desc()).all() if student else []
        )

        # Subject-wise attendance calculation
        subj_attendance = {}
        for s in subjects:
            total = Attendance.query.filter_by(student_id=student.id, subject_id=s.id).count()
            present = Attendance.query.filter_by(
                student_id=student.id, subject_id=s.id, status="Present"
            ).count()
            pct = round((present / total) * 100, 1) if total > 0 else 100.0
            subj_attendance[s.id] = {"total": total, "present": present, "pct": pct}

        assignments = (
            Assignment.query.filter(Assignment.subject_id.in_(subj_ids))
            .order_by(Assignment.due_date.asc())
            .all()
            if subj_ids
            else []
        )
        submissions_map = (
            {sub.assignment_id: sub for sub in student.assignment_submissions.all()}
            if student
            else {}
        )

        tests = (
            Test.query.filter(Test.subject_id.in_(subj_ids), Test.is_published == True)
            .order_by(Test.created_at.desc())
            .all()
            if subj_ids
            else []
        )
        attempts_map = (
            {att.test_id: att for att in student.test_attempts.all()} if student else {}
        )

        return render_template(
            "modules/academics.html",
            is_student=True,
            student=student,
            subjects=subjects,
            syllabi=syllabi,
            attendances=attendances,
            subj_attendance=subj_attendance,
            assignments=assignments,
            submissions_map=submissions_map,
            tests=tests,
            attempts_map=attempts_map,
        )

    else:
        # Teacher perspective
        teacher = current_user.teacher_profile
        assigned_subjects = teacher.subjects if teacher else []
        subj_ids = [s.id for s in assigned_subjects]

        syllabi = (
            Syllabus.query.filter(Syllabus.subject_id.in_(subj_ids)).all() if subj_ids else []
        )
        targets = teacher.targets.all() if teacher else []
        students = (
            Student.query.filter_by(department_id=teacher.department_id)
            .order_by(Student.roll_number)
            .all()
            if teacher
            else []
        )

        assignments = (
            Assignment.query.filter_by(teacher_id=teacher.id)
            .order_by(Assignment.due_date.desc())
            .all()
            if teacher
            else []
        )
        submissions = (
            AssignmentSubmission.query.join(Assignment)
            .filter(Assignment.teacher_id == teacher.id)
            .order_by(AssignmentSubmission.submitted_at.desc())
            .all()
            if teacher
            else []
        )

        tests = (
            Test.query.filter_by(teacher_id=teacher.id).order_by(Test.created_at.desc()).all()
            if teacher
            else []
        )

        return render_template(
            "modules/academics.html",
            is_student=False,
            teacher=teacher,
            subjects=assigned_subjects,
            syllabi=syllabi,
            targets=targets,
            students=students,
            assignments=assignments,
            submissions=submissions,
            tests=tests,
        )


@dashboard_bp.route("/student/tests/<int:test_id>")
@login_required
@role_required("student")
def take_test(test_id: int):
    """Interactive test-taking view for authorized student."""
    student = current_user.student_profile
    test = Test.query.get_or_404(test_id)

    # Check attempt
    attempt = TestAttempt.query.filter_by(test_id=test.id, student_id=student.id).first()
    if attempt and attempt.status == "submitted":
        flash(
            f"You have already submitted this test. Your final score: {attempt.score}/{attempt.total_marks}",
            "info",
        )
        return redirect(url_for("dashboard.academics") + "#tab-tests")

    questions = test.questions.all()
    return render_template(
        "modules/take_test.html",
        test=test,
        student=student,
        questions=questions,
        attempt=attempt,
    )


@dashboard_bp.route("/exams")
@login_required
def exams():
    """Exam Portal module: Timetable, Fee Structure, Results."""
    if current_user.is_student:
        student = current_user.student_profile
        timetables = (
            ExamTimetable.query.filter_by(
                department_id=student.department_id, semester=student.semester
            )
            .order_by(ExamTimetable.exam_date.asc())
            .all()
            if student
            else []
        )
        fees = student.fees.order_by(Fee.due_date.asc()).all() if student else []
        results = student.results.order_by(Result.semester.desc()).all() if student else []

        # SGPA Calculation
        total_obtained = sum(r.total_marks for r in results)
        total_max = sum(r.max_marks for r in results)
        sgpa = round((total_obtained / total_max) * 10, 2) if total_max > 0 else 0.0

        return render_template(
            "modules/exams.html",
            is_student=True,
            student=student,
            timetables=timetables,
            fees=fees,
            results=results,
            sgpa=sgpa,
        )
    else:
        teacher = current_user.teacher_profile
        timetables = (
            ExamTimetable.query.filter_by(department_id=teacher.department_id)
            .order_by(ExamTimetable.exam_date.asc())
            .all()
            if teacher
            else []
        )
        assigned_subj_ids = [s.id for s in teacher.subjects] if teacher else []
        results = (
            Result.query.filter(Result.subject_id.in_(assigned_subj_ids))
            .order_by(Result.created_at.desc())
            .all()
            if assigned_subj_ids
            else []
        )

        return render_template(
            "modules/exams.html",
            is_student=False,
            teacher=teacher,
            timetables=timetables,
            fees=[],
            results=results,
            sgpa=0.0,
        )


@dashboard_bp.route("/feedback")
@login_required
def feedback():
    """Feedback module (Student -> Teacher, Teacher -> Management)."""
    if current_user.is_student:
        student = current_user.student_profile
        teachers = (
            Teacher.query.filter_by(department_id=student.department_id).all() if student else []
        )
        subjects = (
            Subject.query.filter_by(department_id=student.department_id).all() if student else []
        )
        submitted_feedback = (
            student.feedback_given.order_by(Feedback.created_at.desc()).all() if student else []
        )
        return render_template(
            "modules/feedback.html",
            is_student=True,
            teachers=teachers,
            subjects=subjects,
            submitted_feedback=submitted_feedback,
        )
    else:
        teacher = current_user.teacher_profile
        my_feedback = (
            Feedback.query.filter_by(user_id=current_user.id)
            .order_by(Feedback.created_at.desc())
            .all()
        )
        received_feedback = (
            teacher.feedback_received.order_by(Feedback.created_at.desc()).all() if teacher else []
        )
        return render_template(
            "modules/feedback.html",
            is_student=False,
            my_feedback=my_feedback,
            received_feedback=received_feedback,
        )


@dashboard_bp.route("/settings")
@login_required
def settings():
    """User preferences, appearance theme, and account settings."""
    return render_template("modules/settings.html")


@dashboard_bp.route("/profile")
@login_required
def profile():
    """Dynamic profile view for the logged-in user."""
    profile_data = (
        current_user.student_profile if current_user.is_student else current_user.teacher_profile
    )
    return render_template("modules/profile.html", profile=profile_data)


# ── Direct URL Profile Access with Ownership Protection ────────────────────

@dashboard_bp.route("/student/profile/<string:student_id>")
@login_required
@role_required("student")
@owns_student_profile
def student_profile(student_id: str):
    """A student can access ONLY their own profile."""
    return render_template("modules/profile.html", profile=current_user.student_profile)


@dashboard_bp.route("/teacher/profile/<string:teacher_id>")
@login_required
@role_required("teacher")
@owns_teacher_profile
def teacher_profile(teacher_id: str):
    """A teacher can access ONLY their own profile."""
    return render_template("modules/profile.html", profile=current_user.teacher_profile)
