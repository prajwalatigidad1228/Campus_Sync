"""
Campus_Sync – Smart Alert Service (Phase 6)

Generates dynamic, real-time "Things requiring your attention" dashboard alerts
strictly derived from actual database records. Zero invented data.
"""

from datetime import datetime, date, timedelta, timezone
from typing import List, Dict, Any

from app.models.student import Student
from app.models.teacher import Teacher
from app.models.attendance import Attendance
from app.models.assignment import Assignment, AssignmentSubmission
from app.models.fee import Fee
from app.models.announcement import Announcement
from app.models.exam import ExamTimetable
from app.models.result import Result
from app.models.feedback import Feedback
from app.models.test import Test
from app.models.lecture_replacement import LectureReplacementRequest


class AlertService:
    """Computes actionable smart alerts from live database state."""

    @classmethod
    def get_student_alerts(cls, student: Student) -> List[Dict[str, Any]]:
        """
        Calculates alerts for the authenticated student:
        - Low Attendance (<75%)
        - Assignment Due & Unsubmitted
        - Pending Fee Invoices
        - Upcoming Examinations
        - Recent Exam Results
        - Important Announcements
        """
        if not student:
            return []

        alerts: List[Dict[str, Any]] = []

        # ── 1. Attendance Shortage Check ───────────────────────────────────
        overall_pct = student.attendance_percentage
        if student.total_lectures > 0 and overall_pct < 75.0:
            alerts.append({
                "id": "alert_att_overall",
                "severity": "danger",
                "category": "attendance",
                "icon": "⚠️",
                "title": "Attendance Shortage Alert",
                "description": f"Your overall lecture attendance is {overall_pct}%, which is below the mandatory 75% eligibility cutoff.",
                "action_url": "/academics#tab-attendance",
                "action_label": "View Log",
            })
        else:
            # Check subject-specific shortage
            dept_subjects = student.department.subjects.all() if student.department else []
            for s in dept_subjects:
                s_total = Attendance.query.filter_by(student_id=student.id, subject_id=s.id).count()
                if s_total >= 3:
                    s_present = Attendance.query.filter_by(student_id=student.id, subject_id=s.id, status="Present").count()
                    s_pct = round((s_present / s_total) * 100, 1)
                    if s_pct < 75.0:
                        alerts.append({
                            "id": f"alert_att_{s.code}",
                            "severity": "warning",
                            "category": "attendance",
                            "icon": "⚠️",
                            "title": f"Low Attendance in {s.code}",
                            "description": f"You have attended {s_present} of {s_total} lectures ({s_pct}%) in {s.name}.",
                            "action_url": "/academics#tab-attendance",
                            "action_label": "Attendance Register",
                        })

        # ── 2. Pending Assignments ─────────────────────────────────────────
        dept_subj_ids = [s.id for s in student.department.subjects] if student.department else []
        if dept_subj_ids:
            active_assignments = Assignment.query.filter(Assignment.subject_id.in_(dept_subj_ids)).all()
            submitted_ids = {s.assignment_id for s in student.assignment_submissions.all()}
            unsubmitted = [a for a in active_assignments if a.id not in submitted_ids]

            for a in unsubmitted:
                due_str = a.due_date.strftime("%d %b %Y, %I:%M %p") if a.due_date else "Soon"
                alerts.append({
                    "id": f"alert_assign_{a.id}",
                    "severity": "warning",
                    "category": "assignment",
                    "icon": "📝",
                    "title": f"Assignment Due: {a.title}",
                    "description": f"Coursework for {a.subject.code} is awaiting submission. Deadline: {due_str}.",
                    "action_url": "/academics#tab-assignments",
                    "action_label": "Submit Coursework",
                })

        # ── 3. Pending Fee Invoices ────────────────────────────────────────
        pending_fees = student.fees.filter(Fee.status != "Paid").all()
        for f in pending_fees:
            due_str = f.due_date.strftime("%d %b %Y") if f.due_date else "Immediate"
            alerts.append({
                "id": f"alert_fee_{f.id}",
                "severity": "danger" if f.status == "Overdue" else "warning",
                "category": "fee",
                "icon": "💳",
                "title": f"Fee Payment Pending: {f.title}",
                "description": f"Outstanding balance of ${f.remaining_balance:,.2f} due by {due_str}.",
                "action_url": "/exams#tab-fees",
                "action_label": "Pay Online",
            })

        # ── 4. Upcoming Examinations ───────────────────────────────────────
        if dept_subj_ids:
            now_date = date.today()
            upcoming_exams = (
                ExamTimetable.query.filter(
                    ExamTimetable.subject_id.in_(dept_subj_ids),
                    ExamTimetable.exam_date >= now_date,
                )
                .order_by(ExamTimetable.exam_date.asc())
                .limit(2)
                .all()
            )
            for ex in upcoming_exams:
                exam_date_str = ex.exam_date.strftime("%d %b %Y")
                time_range = f"{ex.start_time} - {ex.end_time}"
                alerts.append({
                    "id": f"alert_exam_{ex.id}",
                    "severity": "info",
                    "category": "exam",
                    "icon": "📅",
                    "title": f"Upcoming Exam: {ex.subject.code}",
                    "description": f"{ex.exam_name} on {exam_date_str} ({time_range}) in Room {ex.room_number}.",
                    "action_url": "/exams#tab-timetable",
                    "action_label": "View Timetable",
                })


        # ── 5. Recent Exam Results ─────────────────────────────────────────
        recent_results = (
            student.results.order_by(Result.created_at.desc())
            .limit(1)
            .all()
        )
        for r in recent_results:
            alerts.append({
                "id": f"alert_result_{r.id}",
                "severity": "success",
                "category": "result",
                "icon": "🎓",
                "title": f"Result Published: {r.subject.code}",
                "description": f"You secured Grade {r.grade} ({r.total_marks}/100) in {r.subject.name}.",
                "action_url": "/exams#tab-results",
                "action_label": "View Scorecard",
            })

        # ── 6. Pinned Announcements ────────────────────────────────────────
        pinned_announcements = (
            Announcement.query.filter(
                Announcement.target_role.in_(["all", "student"]),
                Announcement.is_pinned == True,
            )
            .limit(1)
            .all()
        )
        for ann in pinned_announcements:
            alerts.append({
                "id": f"alert_ann_{ann.id}",
                "severity": "info",
                "category": "announcement",
                "icon": "📢",
                "title": f"Notice: {ann.title}",
                "description": ann.content[:130] + ("..." if len(ann.content) > 130 else ""),
                "action_url": "/announcements",
                "action_label": "Read Circular",
            })

        return alerts

    @classmethod
    def get_teacher_alerts(cls, teacher: Teacher) -> List[Dict[str, Any]]:
        """
        Calculates alerts for the authenticated teacher:
        - Assignments awaiting checking / grading
        - Low-attendance students in classes handled
        - Upcoming online tests
        - Pending lecture replacement requests
        - Student feedback received
        - Departmental notices
        """
        if not teacher:
            return []

        alerts: List[Dict[str, Any]] = []

        # ── 1. Pending Assignment Grading ──────────────────────────────────
        pending_count = teacher.pending_grading_count
        if pending_count > 0:
            alerts.append({
                "id": "alert_teacher_grading",
                "severity": "warning",
                "category": "assignment",
                "icon": "📑",
                "title": f"{pending_count} Submission{'s' if pending_count > 1 else ''} Awaiting Grading",
                "description": f"Students have submitted coursework that is ready for assessment and grade allocation.",
                "action_url": "/academics#tab-grading",
                "action_label": "Grade Papers",
            })

        # ── 2. Low-Attendance Students in Handled Subjects ─────────────────
        assigned_subj_ids = [s.id for s in teacher.subjects]
        if assigned_subj_ids:
            # Find students in teacher's department with overall <75% attendance
            dept_students = Student.query.filter_by(department_id=teacher.department_id).all() if teacher.department else []
            low_att_students = [st for st in dept_students if st.total_lectures > 0 and st.attendance_percentage < 75.0]
            if low_att_students:
                names = ", ".join([st.name for st in low_att_students[:3]])
                extra = f" (+{len(low_att_students)-3} others)" if len(low_att_students) > 3 else ""
                alerts.append({
                    "id": "alert_teacher_low_att",
                    "severity": "danger",
                    "category": "attendance",
                    "icon": "⚠️",
                    "title": f"Attendance Warning ({len(low_att_students)} Student{'s' if len(low_att_students) > 1 else ''})",
                    "description": f"Students with attendance below 75%: {names}{extra}. Condonation review may be required.",
                    "action_url": "/academics#tab-attendance",
                    "action_label": "Attendance Register",
                })

        # ── 3. Pending Incoming Lecture Replacement Requests ───────────────
        pending_replacements = (
            teacher.received_replacements.filter_by(status="Pending").all()
        )
        for req in pending_replacements:
            date_str = req.date.strftime("%d %b %Y")
            alerts.append({
                "id": f"alert_teacher_sub_{req.id}",
                "severity": "warning",
                "category": "replacement",
                "icon": "🔄",
                "title": f"Substitution Request: {req.requester.name}",
                "description": f"Requested cover for {req.subject.code} on {date_str} during slot {req.time_slot}.",
                "action_url": "/teacher",
                "action_label": "Review Request",
            })

        # ── 4. Active / Upcoming Online Tests ──────────────────────────────
        if assigned_subj_ids:
            tests = Test.query.filter(
                Test.subject_id.in_(assigned_subj_ids),
                Test.is_published == True,
            ).all()
            for t in tests:
                alerts.append({
                    "id": f"alert_teacher_test_{t.id}",
                    "severity": "info",
                    "category": "test",
                    "icon": "📝",
                    "title": f"Active Quiz: {t.title}",
                    "description": f"{t.subject.code} quiz is live ({t.duration_minutes} mins, {t.total_marks} marks). Total attempts logged: {t.attempts.count()}.",
                    "action_url": "/academics#tab-tests",
                    "action_label": "View Quiz",
                })

        # ── 5. Feedback Received ───────────────────────────────────────────
        recent_feedback = (
            teacher.feedback_received.order_by(Feedback.created_at.desc())
            .limit(1)
            .all()
        )
        for fb in recent_feedback:
            alerts.append({
                "id": f"alert_teacher_fb_{fb.id}",
                "severity": "info",
                "category": "feedback",
                "icon": "⭐",
                "title": "New Student Feedback",
                "description": f"Received a {fb.rating}/5 star evaluation: \"{fb.comments[:90]}...\"",
                "action_url": "/feedback",
                "action_label": "View Feedback",
            })

        # ── 6. Pinned Announcements ────────────────────────────────────────
        pinned_ann = (
            Announcement.query.filter(
                Announcement.target_role.in_(["all", "teacher"]),
                Announcement.is_pinned == True,
            )
            .limit(1)
            .all()
        )
        for ann in pinned_ann:
            alerts.append({
                "id": f"alert_teacher_ann_{ann.id}",
                "severity": "info",
                "category": "announcement",
                "icon": "📢",
                "title": f"Notice: {ann.title}",
                "description": ann.content[:130] + ("..." if len(ann.content) > 130 else ""),
                "action_url": "/announcements",
                "action_label": "Read Circular",
            })

        return alerts
