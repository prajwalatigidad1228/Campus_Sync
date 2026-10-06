"""
Campus_Sync – AI Copilot Controlled Backend Tools (Phase 5)

SECURITY INVARIANT:
The AI Copilot does NOT have direct or arbitrary database access.
All data retrievals are performed via these strongly-scoped Python functions.
A student CANNOT request another student's information through these tools.
A teacher CANNOT request data for subjects they are not authorized to manage.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.models.student import Student
from app.models.teacher import Teacher
from app.models.user import User
from app.models.subject import Subject
from app.models.attendance import Attendance
from app.models.assignment import Assignment, AssignmentSubmission
from app.models.fee import Fee
from app.models.announcement import Announcement
from app.models.syllabus import Syllabus
from app.models.target import TeacherTarget
from app.models.test import Test, Question, TestAttempt
from app.models.exam import ExamTimetable
from app.models.result import Result
from app.models.lecture_replacement import LectureReplacementRequest


class ToolAccessDeniedError(Exception):
    """Raised when an unauthorized data request is attempted."""
    pass


# ── 1. Approved Student Tools ──────────────────────────────────────────────

class StudentCopilotTools:

    @staticmethod
    def get_my_profile(student: Student) -> Dict[str, Any]:
        """Retrieve the authenticated student's profile."""
        if not student:
            raise ToolAccessDeniedError("Student profile not found.")
        return {
            "source": "Your Academic Profile",
            "student_id": student.student_id,
            "name": student.name,
            "department": student.department.name if student.department else "N/A",
            "department_code": student.department.code if student.department else "N/A",
            "semester": student.semester,
            "division": student.division,
            "roll_number": student.roll_number,
            "email": student.email,
        }

    @staticmethod
    def get_my_attendance(student: Student) -> Dict[str, Any]:
        """Retrieve the authenticated student's own attendance statistics and logs."""
        if not student:
            raise ToolAccessDeniedError("Student profile not found.")

        total = student.total_lectures
        present = student.present_lectures
        absent = student.absent_lectures
        pct = student.attendance_percentage

        # Subject-wise breakdown
        dept_subjects = student.department.subjects.all() if student.department else []
        subject_breakdown = []
        for s in dept_subjects:
            s_total = Attendance.query.filter_by(student_id=student.id, subject_id=s.id).count()
            if s_total > 0:
                s_present = Attendance.query.filter_by(student_id=student.id, subject_id=s.id, status="Present").count()
                s_pct = round((s_present / s_total) * 100, 1)
                subject_breakdown.append({
                    "subject": f"{s.code} - {s.name}",
                    "total": s_total,
                    "present": s_present,
                    "percentage": s_pct,
                })

        return {
            "source": "Your Academic Records",
            "overall_percentage": pct,
            "total_lectures": total,
            "present_lectures": present,
            "absent_lectures": absent,
            "subject_breakdown": subject_breakdown,
            "standing": "Good standing" if pct >= 75.0 else "Shortage warning (<75%)",
        }

    @staticmethod
    def get_my_assignments(student: Student) -> Dict[str, Any]:
        """Retrieve the authenticated student's coursework assignments and submission statuses."""
        if not student:
            raise ToolAccessDeniedError("Student profile not found.")

        dept_subj_ids = [s.id for s in student.department.subjects] if student.department else []
        active_assignments = (
            Assignment.query.filter(Assignment.subject_id.in_(dept_subj_ids)).all()
            if dept_subj_ids
            else []
        )
        submissions = {sub.assignment_id: sub for sub in student.assignment_submissions.all()}

        pending_list = []
        submitted_list = []

        for a in active_assignments:
            sub = submissions.get(a.id)
            item = {
                "title": a.title,
                "subject": f"{a.subject.code} - {a.subject.name}",
                "due_date": a.due_date.strftime("%d %b %Y, %I:%M %p") if a.due_date else "N/A",
                "max_marks": a.max_marks,
            }
            if sub:
                item["status"] = sub.status
                item["marks_obtained"] = sub.marks_obtained
                item["feedback"] = sub.feedback
                submitted_list.append(item)
            else:
                item["status"] = "Pending"
                pending_list.append(item)

        return {
            "source": "Your Coursework Assignments",
            "pending_count": len(pending_list),
            "pending_assignments": pending_list,
            "submitted_assignments": submitted_list,
        }

    @staticmethod
    def get_my_results(student: Student) -> Dict[str, Any]:
        """Retrieve the authenticated student's published academic examination results."""
        if not student:
            raise ToolAccessDeniedError("Student profile not found.")

        results = student.results.order_by(Result.semester.desc()).all()
        scorecard = []
        total_obtained = sum(r.total_marks for r in results)
        total_max = sum(r.max_marks for r in results)
        sgpa = round((total_obtained / total_max) * 10, 2) if total_max > 0 else 0.0

        for r in results:
            scorecard.append({
                "subject": f"{r.subject.code} - {r.subject.name}",
                "exam_name": r.exam_name,
                "semester": r.semester,
                "internal_marks": r.internal_marks,
                "external_marks": r.external_marks,
                "total_marks": r.total_marks,
                "max_marks": r.max_marks,
                "grade": r.grade,
                "status": r.status,
            })

        return {
            "source": "Your Official Exam Results",
            "sgpa": sgpa,
            "results_count": len(scorecard),
            "scorecards": scorecard,
        }

    @staticmethod
    def get_my_exams(student: Student) -> Dict[str, Any]:
        """Retrieve the authenticated student's upcoming examination timetable."""
        if not student:
            raise ToolAccessDeniedError("Student profile not found.")

        timetables = (
            ExamTimetable.query.filter_by(
                department_id=student.department_id, semester=student.semester
            )
            .order_by(ExamTimetable.exam_date.asc())
            .all()
        )
        exam_list = []
        for e in timetables:
            exam_list.append({
                "subject": f"{e.subject.code} - {e.subject.name}",
                "exam_name": e.exam_name,
                "date": e.exam_date.strftime("%d %b %Y") if e.exam_date else "N/A",
                "time": f"{e.start_time} - {e.end_time}",
                "room": e.room_number,
            })

        return {
            "source": "Your Exam Timetable",
            "upcoming_exams": exam_list,
        }

    @staticmethod
    def get_my_fees(student: Student) -> Dict[str, Any]:
        """Retrieve the authenticated student's fee invoices, payments, and dues."""
        if not student:
            raise ToolAccessDeniedError("Student profile not found.")

        fees = student.fees.all()
        fee_records = []
        pending_total = 0.0

        for f in fees:
            fee_records.append({
                "title": f.title,
                "type": f.fee_type,
                "amount": f.amount,
                "status": f.status,
                "due_date": f.due_date.strftime("%d %b %Y") if f.due_date else "N/A",
                "receipt_number": f.receipt_number,
            })
            if f.status != "Paid":
                pending_total += f.remaining_balance

        return {
            "source": "Your Institutional Fee Account",
            "pending_balance": pending_total,
            "fee_status": "All Fees Cleared" if pending_total == 0 else f"${pending_total:,.2f} Pending",
            "invoices": fee_records,
        }

    @staticmethod
    def get_my_tests(student: Student) -> Dict[str, Any]:
        """Retrieve online quizzes and test attempts for the authenticated student."""
        if not student:
            raise ToolAccessDeniedError("Student profile not found.")

        dept_subj_ids = [s.id for s in student.department.subjects] if student.department else []
        tests = Test.query.filter(Test.subject_id.in_(dept_subj_ids), Test.is_published == True).all()
        attempts = {att.test_id: att for att in student.test_attempts.all()}

        test_data = []
        for t in tests:
            att = attempts.get(t.id)
            item = {
                "title": t.title,
                "subject": f"{t.subject.code} - {t.subject.name}",
                "duration_minutes": t.duration_minutes,
                "total_marks": t.total_marks,
                "passing_marks": t.passing_marks,
            }
            if att and att.status == "submitted":
                item["status"] = "Completed"
                item["score"] = att.score
                item["percentage"] = att.percentage
            elif att:
                item["status"] = "In Progress"
            else:
                item["status"] = "Available to Take"
            test_data.append(item)

        return {
            "source": "Your Online Tests Portal",
            "tests": test_data,
        }

    @staticmethod
    def get_my_alerts(student: Student) -> Dict[str, Any]:
        """Retrieve actionable smart alerts from live database state."""
        if not student:
            raise ToolAccessDeniedError("Student profile not found.")

        from app.services.alert_service import AlertService
        alerts = AlertService.get_student_alerts(student)
        return {
            "source": "Campus_Sync Smart Alert Center",
            "alert_count": len(alerts),
            "alerts": alerts,
        }



# ── 2. Approved Teacher Tools ──────────────────────────────────────────────

class TeacherCopilotTools:

    @staticmethod
    def get_authorized_class_attendance(teacher: Teacher, subject_code: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve class attendance statistics STRICTLY for subjects assigned to this teacher.
        Rejects requests for subjects not taught by this teacher.
        """
        if not teacher:
            raise ToolAccessDeniedError("Teacher profile not found.")

        assigned_subjects = teacher.subjects
        assigned_map = {s.code.upper(): s for s in assigned_subjects}

        if subject_code:
            code_clean = subject_code.strip().upper()
            if code_clean not in assigned_map:
                raise ToolAccessDeniedError(
                    f"Access Denied: You are not authorized to view attendance for subject '{subject_code}'. "
                    f"You only teach: {', '.join(assigned_map.keys())}."
                )
            target_subjects = [assigned_map[code_clean]]
        else:
            target_subjects = assigned_subjects

        records = []
        for subj in target_subjects:
            total_records = Attendance.query.filter_by(subject_id=subj.id).count()
            present_records = Attendance.query.filter_by(subject_id=subj.id, status="Present").count()
            avg_pct = round((present_records / total_records) * 100, 1) if total_records > 0 else 0.0
            records.append({
                "subject": f"{subj.code} - {subj.name}",
                "total_sessions_marked": total_records,
                "average_attendance_percentage": avg_pct,
            })

        return {
            "source": "Departmental Class Attendance Records",
            "classes": records,
        }

    @staticmethod
    def get_authorized_class_results(teacher: Teacher, subject_code: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve class examination results STRICTLY for subjects assigned to this teacher.
        """
        if not teacher:
            raise ToolAccessDeniedError("Teacher profile not found.")

        assigned_map = {s.code.upper(): s for s in teacher.subjects}

        if subject_code:
            code_clean = subject_code.strip().upper()
            if code_clean not in assigned_map:
                raise ToolAccessDeniedError(
                    f"Access Denied: You are not authorized to view results for '{subject_code}'."
                )
            target_ids = [assigned_map[code_clean].id]
        else:
            target_ids = [s.id for s in teacher.subjects]

        results = Result.query.filter(Result.subject_id.in_(target_ids)).all()
        summary = []
        for r in results:
            summary.append({
                "student_name": r.student.name,
                "roll_number": r.student.roll_number,
                "subject": r.subject.code,
                "exam_name": r.exam_name,
                "total_marks": r.total_marks,
                "grade": r.grade,
                "status": r.status,
            })

        return {
            "source": "Authorized Course Grade Rosters",
            "results_count": len(summary),
            "results": summary,
        }

    @staticmethod
    def get_my_assignments(teacher: Teacher) -> Dict[str, Any]:
        """Retrieve coursework assignments created by this teacher and grading backlog."""
        if not teacher:
            raise ToolAccessDeniedError("Teacher profile not found.")

        assignments = teacher.assignments.all()
        pending_grading = teacher.pending_grading_count
        assign_data = []
        for a in assignments:
            assign_data.append({
                "title": a.title,
                "subject": a.subject.code,
                "due_date": a.due_date.strftime("%d %b %Y") if a.due_date else "N/A",
                "max_marks": a.max_marks,
                "total_submissions": a.submissions.count(),
            })

        return {
            "source": "Your Faculty Assignments Portal",
            "assignments_created": len(assign_data),
            "pending_grading_count": pending_grading,
            "assignments": assign_data,
        }

    @staticmethod
    def get_my_subjects(teacher: Teacher) -> Dict[str, Any]:
        """Retrieve subjects explicitly assigned to this teacher."""
        if not teacher:
            raise ToolAccessDeniedError("Teacher profile not found.")

        subj_list = [f"{s.code} - {s.name} (Semester {s.semester})" for s in teacher.subjects]
        return {
            "source": "Faculty Course Assignment Roster",
            "assigned_subjects": subj_list,
        }

    @staticmethod
    def get_my_targets(teacher: Teacher) -> Dict[str, Any]:
        """Retrieve syllabus delivery milestones and targets."""
        if not teacher:
            raise ToolAccessDeniedError("Teacher profile not found.")

        targets = teacher.targets.all()
        target_list = []
        for tg in targets:
            target_list.append({
                "subject": tg.subject.code,
                "milestone": tg.target_title,
                "completed_hours": tg.completed_lectures,
                "planned_hours": tg.planned_lectures,
                "progress_percentage": tg.progress_percentage,
                "status": tg.status,
            })

        return {
            "source": "Faculty Teaching Targets",
            "overall_progress": teacher.overall_target_progress,
            "targets": target_list,
        }

    @staticmethod
    def get_my_replacement_requests(teacher: Teacher) -> Dict[str, Any]:
        """Retrieve lecture replacement requests sent and received."""
        if not teacher:
            raise ToolAccessDeniedError("Teacher profile not found.")

        incoming = teacher.received_replacements.all()
        sent = teacher.sent_replacements.all()

        return {
            "source": "Faculty Lecture Replacement System",
            "incoming_pending_count": teacher.pending_replacement_requests_count,
            "incoming_requests": [
                {
                    "from": r.requester.name,
                    "subject": r.subject.code,
                    "date": str(r.date),
                    "slot": r.time_slot,
                    "status": r.status,
                }
                for r in incoming
            ],
            "sent_requests": [
                {
                    "to": r.substitute.name,
                    "subject": r.subject.code,
                    "date": str(r.date),
                    "slot": r.time_slot,
                    "status": r.status,
                }
                for r in sent
            ],
        }

    @staticmethod
    def get_my_alerts(teacher: Teacher) -> Dict[str, Any]:
        """Retrieve actionable smart alerts for faculty from live database state."""
        if not teacher:
            raise ToolAccessDeniedError("Teacher profile not found.")

        from app.services.alert_service import AlertService
        alerts = AlertService.get_teacher_alerts(teacher)
        return {
            "source": "Campus_Sync Smart Alert Center",
            "alert_count": len(alerts),
            "alerts": alerts,
        }



# ── 3. Knowledge & Institutional Tools ─────────────────────────────────────

class KnowledgeTools:

    @staticmethod
    def search_announcements(user: User, query: str = "") -> Dict[str, Any]:
        """Search announcements filtered strictly by the user's role authorization."""
        target_roles = ["all", "student"] if user.is_student else ["all", "teacher"]
        q = Announcement.query.filter(Announcement.target_role.in_(target_roles))
        if query:
            q = q.filter(
                (Announcement.title.ilike(f"%{query}%")) | (Announcement.content.ilike(f"%{query}%"))
            )
        announcements = q.order_by(Announcement.is_pinned.desc(), Announcement.created_at.desc()).limit(5).all()

        results = []
        for a in announcements:
            results.append({
                "title": a.title,
                "category": a.category,
                "content": a.content,
                "date": a.created_at.strftime("%d %b %Y") if a.created_at else "N/A",
                "pinned": a.is_pinned,
            })

        return {
            "source": "Campus Announcements Feed",
            "announcements": results,
        }

    @staticmethod
    def search_syllabus(user: User, subject_code: Optional[str] = None) -> Dict[str, Any]:
        """Search curriculum syllabus units authorized for the user's department."""
        dept_id = None
        if user.is_student and user.student_profile:
            dept_id = user.student_profile.department_id
        elif user.is_teacher and user.teacher_profile:
            dept_id = user.teacher_profile.department_id

        if not dept_id:
            return {"source": "Course Curriculum", "units": []}

        q = Syllabus.query.join(Subject).filter(Subject.department_id == dept_id)
        if subject_code:
            q = q.filter(Subject.code.ilike(f"%{subject_code.strip()}%"))

        units = q.order_by(Subject.code, Syllabus.unit_number).all()
        unit_list = []
        for u in units:
            unit_list.append({
                "subject": f"{u.subject.code} - {u.subject.name}",
                "unit": f"Unit {u.unit_number}: {u.unit_title}",
                "topics": u.topics,
                "status": u.completion_status,
            })

        return {
            "source": "Academic Syllabus 2025-26",
            "units": unit_list,
        }
