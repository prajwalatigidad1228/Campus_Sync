"""
Campus_Sync – Comprehensive Database Seeder (Development Only)
Populates realistic demo data for all Phase 4 models:
Departments, Subjects, Syllabi, Users, Students, Teachers, Targets,
Attendance, Assignments, Online Tests, Fees, Timetables, Results,
Announcements, Feedback, and Lecture Replacement Requests.

Demo credentials:
  Student 1 : student@test.com  /  Student@123
  Student 2 : student2@test.com /  Student@123
  Teacher 1 : teacher@test.com  /  Teacher@123
  Teacher 2 : teacher2@test.com /  Teacher@123
"""

from datetime import datetime, timezone, date, timedelta
from app.database.db import db
from app.models import (
    User, Role,
    Department, Subject,
    Student, Teacher,
    Attendance,
    Assignment, AssignmentSubmission,
    Fee,
    Announcement,
    Syllabus,
    TeacherTarget,
    Test, Question, TestAttempt, TestAnswer,
    ExamTimetable,
    Result,
    Feedback,
    LectureReplacementRequest,
)


def seed_all(app=None):
    """Seed the database with comprehensive realistic demo data."""
    from flask import has_app_context
    if not has_app_context():
        if app is None:
            from run import app as fallback_app
            app = fallback_app
        with app.app_context():
            return _seed_all_body()
    return _seed_all_body()


def _seed_all_body():
    print("\n" + "=" * 55)
    print("  Campus_Sync - Database Seeder (Phase 4)")
    print("=" * 55)

    # ── 1. Departments ───────────────────────────────────────────────────────
    dept_cs = Department.query.filter_by(code="CS").first()

    if not dept_cs:
        dept_cs = Department(
            name="Computer Science & Engineering",
            code="CS",
            description="Undergraduate and postgraduate programs in computer science and engineering.",
        )
        db.session.add(dept_cs)
        db.session.flush()
        print("  [+] Department: Computer Science & Engineering (CS)")

    dept_it = Department.query.filter_by(code="IT").first()
    if not dept_it:
        dept_it = Department(
            name="Information Technology",
            code="IT",
            description="Programs in information systems and cyber security.",
        )
        db.session.add(dept_it)
        db.session.flush()
        print("  [+] Department: Information Technology (IT)")

    # ── 2. Subjects ──────────────────────────────────────────────────────────
    subjects_data = [
        {"name": "Data Structures & Algorithms", "code": "CS201", "semester": 3, "dept": dept_cs},
        {"name": "Database Management Systems", "code": "CS301", "semester": 5, "dept": dept_cs},
        {"name": "Computer Networks", "code": "CS302", "semester": 5, "dept": dept_cs},
        {"name": "Machine Learning & AI", "code": "CS401", "semester": 7, "dept": dept_cs},
    ]
    created_subjects = {}
    for sd in subjects_data:
        subj = Subject.query.filter_by(code=sd["code"], department_id=sd["dept"].id).first()
        if not subj:
            subj = Subject(
                name=sd["name"],
                code=sd["code"],
                semester=sd["semester"],
                department_id=sd["dept"].id,
            )
            db.session.add(subj)
            db.session.flush()
            print(f"  [+] Subject: {sd['code']} – {sd['name']}")
        created_subjects[sd["code"]] = subj

    # ── 3. Syllabi Units ─────────────────────────────────────────────────────
    cs301 = created_subjects["CS301"]
    if cs301 and Syllabus.query.filter_by(subject_id=cs301.id).count() == 0:
        units = [
            (1, "Introduction to DBMS & Relational Model", "ER Modeling, relational schemas, keys, constraints.", 8, "Completed"),
            (2, "SQL, Triggers & Views", "DDL/DML, complex JOINs, aggregate queries, triggers and stored procedures.", 10, "Completed"),
            (3, "Relational Algebra & Normalization", "Functional dependencies, 1NF, 2NF, 3NF, BCNF, lossless joins.", 10, "In Progress"),
            (4, "Transaction Management & ACID Properties", "Serializability, concurrency control, 2PL, deadlock prevention.", 8, "Pending"),
            (5, "Storage Structures & Query Optimization", "B+ Trees, hashing, indexing, execution plans.", 6, "Pending"),
        ]
        for num, title, topics, hrs, status in units:
            syl = Syllabus(
                subject_id=cs301.id,
                unit_number=num,
                unit_title=title,
                topics=topics,
                hours_allocated=hrs,
                completion_status=status,
            )
            db.session.add(syl)
        print("  [+] Syllabi units created for CS301")

    # ── 4. Users & Profiles ──────────────────────────────────────────────────
    user_stu1 = _get_or_create_user("student@test.com", "Student@123", Role.STUDENT)
    user_stu2 = _get_or_create_user("riya@test.com", "Student@123", Role.STUDENT)
    user_tch1 = _get_or_create_user("teacher@test.com", "Teacher@123", Role.TEACHER)
    user_tch2 = _get_or_create_user("teacher2@test.com", "Teacher@123", Role.TEACHER)


    # Student 1: Aarav Sharma
    stu1 = Student.query.filter_by(user_id=user_stu1.id).first()
    if not stu1:
        stu1 = Student(
            student_id="STU-2024-001",
            user_id=user_stu1.id,
            name="Alex Johnson",
            phone="+91-9876543210",
            address="12, Elm Street, Mumbai, Maharashtra",
            bio="Junior CSE student passionate about Distributed Systems & AI.",
            department_id=dept_cs.id,
            semester=5,
            division="A",
            roll_number="CS-A-42",
        )
        db.session.add(stu1)
        db.session.flush()
        print("  [+] Student: Alex Johnson (STU-2024-001)")

    # Student 2: Riya Sen
    stu2 = Student.query.filter_by(user_id=user_stu2.id).first()
    if not stu2:
        stu2 = Student(
            student_id="STU-2024-015",
            user_id=user_stu2.id,
            name="Riya Sen",
            phone="+91-9876543211",
            address="45, Park Avenue, Pune, Maharashtra",
            bio="Interested in Cloud Computing and Cybersecurity.",
            department_id=dept_cs.id,
            semester=5,
            division="A",
            roll_number="CS-A-15",
        )
        db.session.add(stu2)
        db.session.flush()
        print("  [+] Student: Riya Sen (STU-2024-015)")

    # Teacher 1: Dr. Priya Sharma (teaches CS301, CS401)
    tch1 = Teacher.query.filter_by(user_id=user_tch1.id).first()
    if not tch1:
        tch1 = Teacher(
            teacher_id="TCH-2024-001",
            user_id=user_tch1.id,
            name="Dr. Priya Sharma",
            phone="+91-9123456789",
            designation="Associate Professor",
            bio="12+ years teaching Database Systems, Big Data Analytics, and AI.",
            department_id=dept_cs.id,
        )
        tch1.subjects = [created_subjects["CS301"], created_subjects["CS401"]]
        db.session.add(tch1)
        db.session.flush()
        print("  [+] Teacher: Dr. Priya Sharma (TCH-2024-001)")

    # Teacher 2: Prof. Rajesh Nair (teaches CS201, CS302)
    tch2 = Teacher.query.filter_by(user_id=user_tch2.id).first()
    if not tch2:
        tch2 = Teacher(
            teacher_id="TCH-2024-002",
            user_id=user_tch2.id,
            name="Prof. Rajesh Nair",
            phone="+91-9123456780",
            designation="Assistant Professor",
            bio="Specialist in Computer Networks and Algorithms.",
            department_id=dept_cs.id,
        )
        tch2.subjects = [created_subjects["CS201"], created_subjects["CS302"]]
        db.session.add(tch2)
        db.session.flush()
        print("  [+] Teacher: Prof. Rajesh Nair (TCH-2024-002)")

    # ── 5. Teacher Targets ───────────────────────────────────────────────────
    if TeacherTarget.query.filter_by(teacher_id=tch1.id).count() == 0:
        tg1 = TeacherTarget(
            teacher_id=tch1.id,
            subject_id=created_subjects["CS301"].id,
            target_title="Complete Unit 3 (Normalization) by Week 6",
            planned_lectures=14,
            completed_lectures=11,
            target_date=date.today() + timedelta(days=10),
            status="On Track",
            remarks="Completed 3NF; BCNF decomposition lecture scheduled on Friday.",
        )
        tg2 = TeacherTarget(
            teacher_id=tch1.id,
            subject_id=created_subjects["CS401"].id,
            target_title="Deliver Feature Engineering Lab Modules",
            planned_lectures=10,
            completed_lectures=8,
            target_date=date.today() + timedelta(days=15),
            status="On Track",
            remarks="Supervised ML lab sessions finished.",
        )
        db.session.add_all([tg1, tg2])
        print("  [+] Teacher targets created for Dr. Priya Patel")

    # ── 6. Attendance Records ────────────────────────────────────────────────
    if Attendance.query.filter_by(student_id=stu1.id).count() == 0:
        # Create 14 realistic lecture dates yielding ~86% attendance
        base_date = date.today() - timedelta(days=25)
        for i in range(14):
            att_date = base_date + timedelta(days=i)
            # Sunday or Saturday skip
            if att_date.weekday() >= 5:
                continue
            # Give present on most, absent on 2
            status = "Absent" if i in (3, 9) else "Present"
            att = Attendance(
                student_id=stu1.id,
                subject_id=created_subjects["CS301"].id,
                teacher_id=tch1.id,
                date=att_date,
                status=status,
                remarks="Regular class" if status == "Present" else "Medical absence",
            )
            db.session.add(att)

            # Also attendance for Student 2
            att2 = Attendance(
                student_id=stu2.id,
                subject_id=created_subjects["CS301"].id,
                teacher_id=tch1.id,
                date=att_date,
                status="Present",
                remarks="Regular class",
            )
            db.session.add(att2)
        print("  [+] Attendance records seeded (~86% attendance rate)")

    # ── 7. Assignments & Submissions ─────────────────────────────────────────
    assign1 = Assignment.query.filter_by(title="Relational Algebra & Advanced SQL").first()
    if not assign1:
        assign1 = Assignment(
            subject_id=created_subjects["CS301"].id,
            teacher_id=tch1.id,
            title="Relational Algebra & Advanced SQL",
            description="Solve set operations, correlated subqueries, and window functions on the University schema.",
            due_date=datetime.now(timezone.utc) + timedelta(days=5),
            max_marks=100.0,
        )
        assign2 = Assignment(
            subject_id=created_subjects["CS301"].id,
            teacher_id=tch1.id,
            title="Schema Normalization & Dependency Preserving",
            description="Decompose given relations into 3NF and BCNF. Provide minimal cover proofs.",
            due_date=datetime.now(timezone.utc) - timedelta(days=2),
            max_marks=50.0,
        )
        assign3 = Assignment(
            subject_id=created_subjects["CS302"].id,
            teacher_id=tch2.id,
            title="Multi-Threaded Socket Server in Python",
            description="Implement concurrent TCP chat server handling multiple clients with epoll or select.",
            due_date=datetime.now(timezone.utc) + timedelta(days=8),
            max_marks=50.0,
        )
        db.session.add_all([assign1, assign2, assign3])
        db.session.flush()

        # Student 1 submitted Assignment 2 and received grade
        sub1 = AssignmentSubmission(
            assignment_id=assign2.id,
            student_id=stu1.id,
            submission_text="Solution uploaded with full proof steps and dependency matrix.",
            attachment_url="https://github.com/campus-sync-solutions/assignment-2",
            submitted_at=datetime.now(timezone.utc) - timedelta(days=3),
            marks_obtained=47.5,
            feedback="Excellent mathematical rigor on minimal cover.",
            graded_at=datetime.now(timezone.utc) - timedelta(days=1),
            status="Graded",
        )
        # Student 2 submitted Assignment 1 (pending teacher grading)
        sub2 = AssignmentSubmission(
            assignment_id=assign1.id,
            student_id=stu2.id,
            submission_text="Queries written and tested on PostgreSQL 15.",
            attachment_url="https://github.com/riya-sen/cs301-sql",
            submitted_at=datetime.now(timezone.utc) - timedelta(hours=6),
            status="Submitted",
        )
        db.session.add_all([sub1, sub2])
        print("  [+] Coursework assignments and student submissions created")

    # ── 8. Online Tests & Attempts ───────────────────────────────────────────
    test1 = Test.query.filter_by(title="Mid-Semester DBMS Quiz").first()
    if not test1:
        test1 = Test(
            subject_id=created_subjects["CS301"].id,
            teacher_id=tch1.id,
            title="Mid-Semester DBMS Quiz",
            description="Evaluates understanding of Keys, Normal forms, and SQL constraints.",
            duration_minutes=15,
            total_marks=5.0,
            passing_marks=2.0,
            is_published=True,
        )
        db.session.add(test1)
        db.session.flush()

        questions_data = [
            ("Which of the following is NOT an ACID property?", "Atomicity", "Consistency", "Isolation", "Durability / Availability", "D"),
            ("A relation where every non-key attribute is fully functionally dependent on the primary key is in:", "1NF", "2NF", "3NF", "BCNF", "B"),
            ("Which SQL clause is used to filter aggregated groups?", "WHERE", "HAVING", "GROUP BY", "ORDER BY", "B"),
            ("In relational algebra, which operator selects rows satisfying a condition?", "Projection (π)", "Selection (σ)", "Cartesian Product (×)", "Join (⨝)", "B"),
            ("Which index structure maintains sorted keys in balanced multi-way leaves?", "B+ Tree", "Hash Table", "Binary Search Tree", "Linked List", "A"),
        ]
        created_q = []
        for idx, (qtext, oa, ob, oc, od, ans) in enumerate(questions_data):
            q = Question(
                test_id=test1.id,
                question_text=qtext,
                option_a=oa,
                option_b=ob,
                option_c=oc,
                option_d=od,
                correct_option=ans,
                marks=1.0,
                order_index=idx,
            )
            db.session.add(q)
            created_q.append(q)
        db.session.flush()

        # Student 1 attempt already completed with 4/5 score
        att1 = TestAttempt(
            test_id=test1.id,
            student_id=stu1.id,
            started_at=datetime.now(timezone.utc) - timedelta(days=1, hours=2),
            submitted_at=datetime.now(timezone.utc) - timedelta(days=1, hours=1, minutes=48),
            score=4.0,
            total_marks=5.0,
            status="submitted",
        )
        db.session.add(att1)
        db.session.flush()

        # Add second test that is open to take
        test2 = Test(
            subject_id=created_subjects["CS301"].id,
            teacher_id=tch1.id,
            title="SQL Indexing & Query Plans Practice Quiz",
            description="3-question quick check on B-Trees, sequential scans, and index lookups.",
            duration_minutes=10,
            total_marks=3.0,
            passing_marks=1.5,
            is_published=True,
        )
        db.session.add(test2)
        db.session.flush()

        test2_q = [
            ("What type of scan is performed when no suitable index exists on a large table?", "Index Only Scan", "Sequential / Full Table Scan", "Bitmap Scan", "Tid Scan", "B"),
            ("Which SQL command explains the query execution plan in PostgreSQL?", "EXPLAIN ANALYZE", "DESCRIBE PLAN", "SHOW COST", "PLAN RUN", "A"),
            ("A Clustered Index alters the physical order of data on disk. How many can exist per table?", "1", "2", "Unlimited", "0", "A"),
        ]
        for idx, (qt, a, b, c, d, ans) in enumerate(test2_q):
            q = Question(
                test_id=test2.id,
                question_text=qt,
                option_a=a,
                option_b=b,
                option_c=c,
                option_d=d,
                correct_option=ans,
                marks=1.0,
                order_index=idx,
            )
            db.session.add(q)

        print("  [+] Online tests and questions created")

    # ── 9. Fee Structure ─────────────────────────────────────────────────────
    if Fee.query.filter_by(student_id=stu1.id).count() == 0:
        fees = [
            ("Semester 5 Tuition & Academic Fee", "Tuition", 4500.0, 4500.0, date.today() - timedelta(days=60), "Paid", "REC-2025-0012-TUI", datetime.now(timezone.utc) - timedelta(days=60)),
            ("Midterm Examination Registration Fee", "Exam", 250.0, 250.0, date.today() - timedelta(days=20), "Paid", "REC-2025-0045-EXM", datetime.now(timezone.utc) - timedelta(days=20)),
            ("Central Computing & Laboratory Charges", "Laboratory", 350.0, 0.0, date.today() + timedelta(days=30), "Pending", None, None),
            ("Student Library & Digital Portal Access", "Library", 120.0, 120.0, date.today() - timedelta(days=90), "Paid", "REC-2025-0089-LIB", datetime.now(timezone.utc) - timedelta(days=90)),
        ]
        for title, ftype, amt, paid, due, status, rec, paid_at in fees:
            f = Fee(
                student_id=stu1.id,
                title=title,
                fee_type=ftype,
                amount=amt,
                amount_paid=paid,
                due_date=due,
                status=status,
                receipt_number=rec,
                paid_at=paid_at,
                semester=5,
                academic_year="2025-26",
            )
            db.session.add(f)
        print("  [+] Fee records created with receipts and pending balances")

    # ── 10. Exam Timetable ───────────────────────────────────────────────────
    if ExamTimetable.query.filter_by(department_id=dept_cs.id).count() == 0:
        exams = [
            ("CS301", "Database Management Systems", date.today() + timedelta(days=14), "10:00 AM", "01:00 PM", "Hall 302", 5),
            ("CS302", "Computer Networks", date.today() + timedelta(days=16), "10:00 AM", "01:00 PM", "Hall 302", 5),
            ("CS201", "Data Structures & Algorithms", date.today() + timedelta(days=18), "02:00 PM", "05:00 PM", "Hall 101", 3),
        ]
        for code, name, edate, st, et, room, sem in exams:
            tt = ExamTimetable(
                department_id=dept_cs.id,
                subject_id=created_subjects[code].id,
                exam_name="Mid-Semester Theory Examination",
                exam_date=edate,
                start_time=st,
                end_time=et,
                room_number=room,
                semester=sem,
            )
            db.session.add(tt)
        print("  [+] Examination timetable scheduled")

    # ── 11. Results ──────────────────────────────────────────────────────────
    if Result.query.filter_by(student_id=stu1.id).count() == 0:
        results = [
            ("CS201", "Semester 4 University Exams", 28.5, 63.5, 92.0, 100.0, "O", "Pass", 4),
            ("CS301", "Midterm Assessment 2026", 27.0, 61.0, 88.0, 100.0, "A+", "Pass", 5),
            ("CS302", "Midterm Assessment 2026", 26.0, 58.0, 84.0, 100.0, "A", "Pass", 5),
        ]
        for code, exname, internal, external, tot, mx, grade, status, sem in results:
            res = Result(
                student_id=stu1.id,
                subject_id=created_subjects[code].id,
                exam_name=exname,
                internal_marks=internal,
                external_marks=external,
                total_marks=tot,
                max_marks=mx,
                grade=grade,
                status=status,
                semester=sem,
                academic_year="2025-26",
            )
            db.session.add(res)
        print("  [+] Academic scorecards and results created (SGPA calculated)")

    # ── 12. Announcements ────────────────────────────────────────────────────
    if Announcement.query.count() == 0:
        announcements = [
            ("Mid-Semester Academic Break and Hall Ticket Issuance", "All undergraduate engineering students must download their official hall tickets before the cutoff date. Examination hall entry strictly requires verified ID cards.", "College Management", "all", user_tch1.id, True),
            ("CS301 Query Optimization Practice Test Now Live", "Dear students, practice Quiz 2 is available on the Academics Portal. Complete the questions before next Monday's lab.", "Teachers", "student", user_tch1.id, False),
            ("Smart Campus Hackathon 2026 – Team Registration Open", "Inter-college hackathon hosted by the IEEE Student Branch. Cash prizes up to $5,000. Form teams of 3-4 members and register on the student portal.", "Student Coordinators", "all", user_stu1.id, False),
        ]
        for title, content, cat, role_tgt, auth_id, pinned in announcements:
            ann = Announcement(
                title=title,
                content=content,
                category=cat,
                target_role=role_tgt,
                author_id=auth_id,
                department_id=dept_cs.id,
                is_pinned=pinned,
            )
            db.session.add(ann)
        print("  [+] Department and college announcements created")

    # ── 13. Feedback ─────────────────────────────────────────────────────────
    if Feedback.query.count() == 0:
        fb1 = Feedback(
            feedback_type="student_to_teacher",
            user_id=user_stu1.id,
            student_id=stu1.id,
            teacher_id=tch1.id,
            subject_id=created_subjects["CS301"].id,
            category="Teaching Quality",
            rating=5,
            comments="Very clear explanations of relational algebra and normalization algorithms.",
            is_anonymous=False,
            status="Reviewed",
        )
        fb2 = Feedback(
            feedback_type="teacher_to_management",
            user_id=user_tch1.id,
            category="Classroom & Lab Infrastructure",
            rating=4,
            comments="Request additional GPU instances in Lab 4 for Machine Learning semester projects.",
            is_anonymous=False,
            status="Submitted",
        )
        db.session.add_all([fb1, fb2])
        print("  [+] Realistic feedback records submitted")

    # ── 14. Lecture Replacement Requests ─────────────────────────────────────
    if LectureReplacementRequest.query.count() == 0:
        req = LectureReplacementRequest(
            requester_id=tch1.id,
            substitute_id=tch2.id,
            subject_id=created_subjects["CS301"].id,
            date=date.today() + timedelta(days=4),
            time_slot="10:00 AM - 11:00 AM",
            reason="Attending National Computing Symposium conference as keynote speaker.",
            status="Pending",
        )
        db.session.add(req)
        print("  [+] Lecture replacement request created between faculty")

    db.session.commit()

    print("\n  Demo Credentials (development only):")
    print("  +----------------------------------------------------+")
    print("  |  student@test.com   /  Student@123  (Alex Johnson) |")
    print("  |  riya@test.com      /  Student@123  (Riya Sen)     |")
    print("  |  teacher@test.com   /  Teacher@123  (Dr. Priya)    |")
    print("  |  teacher2@test.com  /  Teacher@123  (Prof. Rajesh) |")
    print("  +----------------------------------------------------+")
    print("=" * 55 + "\n")


def _get_or_create_user(email: str, password: str, role: Role) -> User:
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        print(f"  [+] User: {email} [{role.value}]")
    return user
