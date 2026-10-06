# 🎓 Campus_Sync

> A modern, secure, and intuitive **College Management + Institute-Aware AI Copilot** platform.

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.x-D71F00?logo=sqlalchemy&logoColor=white)](https://sqlalchemy.org)
[![Security](https://img.shields.io/badge/Security-Hardened%20(RBAC%20%2B%20CSP)-2ea44f)](SECURITY.md)
[![Tests](https://img.shields.io/badge/Tests-125%20Passed%20%2F%200%20Failed-success)](tests/)
[![UI Style](https://img.shields.io/badge/UI-MediPlant--Inspired-059669)](templates/)

---

## 📌 Project Overview

**Campus_Sync** is an institutional digital campus operating system designed to eliminate academic friction for students, faculty, and administrators. Built with a high-end, responsive MediPlant-inspired interface, it integrates day-to-day academic workflows (attendance, grading, coursework, online exams, fee payments, and timetable scheduling) with an **Authorization-First AI Copilot** backed by **Retrieval-Augmented Generation (RAG)**.

### Core Pillars
1. **Strict Two-Role RBAC**: Isolated, dedicated portals for **Students** and **Teachers** with zero permission leakage.
2. **Authorized AI Copilot**: Institute-aware intelligence that checks user role and access permissions *before* data reaches the model. Arbitrary SQL execution is strictly forbidden.
3. **Institutional RAG**: Grounded retrieval from authoritative college policy handbooks, attendance cutoffs, examination statutes, and academic calendars.
4. **Smart Alerts ("Things requiring your attention")**: Real-time, DB-driven priority alerts tailored dynamically to each user.
5. **Robust Security Sandbox**: File uploads verified with magic-byte analysis, path-traversal sanitization, anti-session-fixation defenses, and HTTP security headers.

---

## 🌟 Key Features

### 👨‍🎓 Student Experience
- **Personal Dashboard**: Live attendance rates, pending assignment counters, fee balances, and prioritized smart alerts.
- **Academics Portal**: Enrolled course syllabi (units & status), lecture attendance logs, and coursework submissions.
- **Online Tests & Instant Grading**: Interactive MCQ and coding quiz taking with immediate score calculation and attempt protection.
- **Examinations & Fees**: Published semester examination scorecards, calculated SGPA, schedule timetables, and online fee payment with receipt generation.
- **Coursework Uploads**: Secure file submission pipeline with sandbox storage and extension validation.
- **Institutional Feedback**: Anonymous course evaluation and faculty feedback submission.

### 👩‍🏫 Teacher / Faculty Experience
- **Faculty Dashboard**: Live syllabus delivery targets, pending submission checking queues, and incoming peer replacement requests.
- **Attendance Register**: Class-wide attendance recording for authorized subjects with session timestamps.
- **Assignment Management**: Coursework creation with deadlines, submission grading, score assignment, and qualitative feedback.
- **Lecture Replacement Coordination**: Peer substitution request workflow between faculty members (Create, Review, Accept/Reject).
- **Target Tracking**: Structured milestones tracking planned vs. completed curriculum lecture hours.
- **Course Analytics & Grade Rosters**: Authorized grade sheets and performance summaries.

### 🤖 AI College Copilot (Institute-Aware)
- **Controlled Backend Tools**:
  - `get_my_profile()`, `get_my_attendance()`, `get_my_assignments()`, `get_my_results()`, `get_my_fees()`, `get_my_exams()`, `get_my_alerts()`
  - `get_authorized_class_attendance()`, `get_authorized_class_results()`, `get_my_targets()`
- **Authoritative Policy RAG**: Accurate citations from official college documents:
  - *Attendance & Condonation Regulations 2026*
  - *Examination Conduct & Hall Ticket Rules*
  - *Academic Calendar Fall 2026*
  - *Faculty Guidelines & Lecture Replacement Regulations*
- **Guardrail Enforcements**:
  - Pre-screening blocks prompt injections, jailbreaks, and instructions overrides.
  - Cross-student data requests ("Show Riya's marks") are immediately refused.
  - Faculty salary and confidential administrative data are protected.
  - Teacher class queries enforce course assignments before retrieval (e.g. CS301 authorized vs CS201 denied).

---

## 🏛️ System Architecture

```
Campus_Sync/
├── app/
│   ├── ai/                         # AI Copilot & Knowledge Retrieval
│   │   ├── copilot_engine.py       # Central orchestrator & intent router
│   │   ├── guardrails.py           # Prompt injection & privacy filter
│   │   ├── llm_service.py          # Deterministic & remote LLM providers
│   │   ├── rag_engine.py           # Institutional vector similarity retrieval
│   │   └── tools.py                # Role-scoped authorized DB access tools
│   ├── auth/                       # Authentication & Access Control
│   │   ├── decorators.py           # @role_required, @owns_profile decorators
│   │   └── forms.py                # Login & input validation forms
│   ├── database/                   # Database Engine & Setup
│   │   ├── db.py                   # SQLAlchemy instance
│   │   └── seeder.py               # Comprehensive realistic demo data seeder
│   ├── models/                     # SQLAlchemy ORM Models
│   │   ├── user.py                 # User & Role enum (Student, Teacher)
│   │   ├── student.py              # Student profile & relationships
│   │   ├── teacher.py              # Teacher profile & assigned courses
│   │   ├── department.py           # Academic departments
│   │   ├── subject.py              # Courses and course codes
│   │   ├── attendance.py           # Lecture attendance sessions
│   │   ├── assignment.py           # Assignments & Student submissions
│   │   ├── fee.py                  # Fee invoices & receipts
│   │   ├── test.py                 # Online quizzes, questions & attempts
│   │   ├── exam.py                 # Exam timetable schedules
│   │   ├── result.py               # Grade cards, SGPA, total marks
│   │   ├── target.py               # Faculty curriculum milestones
│   │   ├── announcement.py         # Administrative notices & circulars
│   │   ├── feedback.py             # Course feedback records
│   │   ├── lecture_replacement.py  # Faculty substitution requests
│   │   └── upload.py               # Secure file upload records
│   ├── routes/                     # Blueprint Modular Controllers
│   │   ├── main.py                 # Public landing page (/)
│   │   ├── auth.py                 # /login, /logout session handlers
│   │   ├── dashboard.py            # /student, /teacher, /academics, /exams
│   │   ├── college_api.py          # /api/* action endpoints
│   │   ├── copilot_api.py          # /api/copilot/chat, /clear
│   │   ├── upload_api.py           # /api/uploads/file, /download
│   │   └── health.py               # /api/health, /api/status
│   ├── services/                   # Business Logic & DB Transactions
│   │   ├── alert_service.py        # Dynamic smart alerts engine
│   │   ├── college_service.py      # Core academic service functions
│   │   └── seeder.py               # Database seeder orchestration
│   ├── utils/                      # Utilities & Middleware
│   │   ├── error_handlers.py       # Custom 400, 403, 404, 500 handlers
│   │   ├── security_headers.py     # CSP, nosniff, SAMEORIGIN middleware
│   │   └── upload_security.py      # Magic byte validation & file sandbox
│   └── config.py                   # Multi-environment configurations
├── static/                         # Assets (CSS, JS, Icons)
│   ├── css/main.css                # MediPlant custom responsive theme
│   └── js/main.js                  # Frontend interactions & Copilot widget
├── templates/                      # Jinja2 Modular Views
│   ├── base.html                   # Base layout
│   ├── app_layout.html             # Dashboard shell with sidebar & header
│   ├── auth/login.html             # Clean authentication interface
│   ├── dashboard/                  # Student & Teacher portal views
│   ├── modules/                    # Academics, Exams, Copilot, Feedback
│   └── errors/                     # Friendly error templates (400, 403, 404, 500)
├── tests/                          # Automated Pytest Suites (125 tests)
├── uploads/                        # Non-executable file sandbox (gitignored)
├── requirements.txt                # Production dependencies
├── run.py                          # Server launcher
├── SECURITY.md                     # Security audit & specifications
└── README.md                       # Documentation
```

---

## 🔒 Security & Authorization Model

For the complete technical specification, refer to [`SECURITY.md`](SECURITY.md).

### Pre-Retrieval Copilot Architecture
```
User Query
    │
    ▼
Determine Intent
    │
    ├─────────────────────────────────┬──────────────────────────────────┐
    ▼                                 ▼                                  ▼
Policy Question                   Data Question                   General / Unknown
    │                                 │                                  │
Institutional RAG             Identify Resource                 Mandatory Fallback
(`Attendance Regulations 2026`)       │                        (`FALLBACK_MESSAGE`)
                              Check Authorization
                                      │
                         ┌────────────┴────────────┐
                         ▼                         ▼
                      Allowed                   Denied
                         │                         │
                  Database Tool             Immediate DENY
             (`get_authorized_...`)    (`Role Authorization Enforcer`)
                                       *NO Fallback to RAG*
```

### Defense Highlights
- **Session Security**: Session fixation defense via `session.clear()` on login and logout. Cookies set with `HttpOnly`, `SameSite=Lax`, and `Secure` (production).
- **IDOR Protection**: All object references verify current user ownership (e.g. `/student/profile/<id>`, `/api/fees/<id>/pay`, file downloads).
- **Upload Sandbox**: Extension whitelisting (`.pdf`, `.png`, `.jpg`, `.jpeg`, `.docx`, `.zip`), binary magic-byte inspection, UUID filename randomization, and path-traversal sanitization.
- **HTTP Headers**: Injected on every response: `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, `X-XSS-Protection: 1; mode=block`, `Referrer-Policy: strict-origin-when-cross-origin`, and `Content-Security-Policy`.
- **Zero Raw Traces**: Custom 400, 403, 404, and 500 handlers ensure normal users never see raw Python stack traces.

---

## 💻 Tech Stack

| Component | Technology | Rationale |
| :--- | :--- | :--- |
| **Backend Language** | Python 3.12 | Modern, typed, performant |
| **Web Framework** | Flask 3.x | Lightweight, modular blueprint architecture |
| **ORM & Database** | SQLAlchemy 2.x / SQLite (dev) / PostgreSQL (prod) | Reliable relational schema, clean migrations |
| **Authentication** | Flask-Login + Bcrypt | Secure password hashing & session management |
| **AI Intelligence** | Local Deterministic Engine + Remote Fallback | 100% offline-compatible; zero external paid API lock-in |
| **Vector Retrieval** | TF-IDF Vector Space / Cosine Similarity | Fast, zero-overhead RAG knowledge grounding |
| **Frontend Layout** | Jinja2, HTML5, Modern CSS, Vanilla JS | MediPlant design standard, zero framework bloat |
| **Testing Suite** | Pytest + pytest-flask | 125 comprehensive unit, integration & E2E tests |

---

## ⚡ Quickstart & Installation

### 1. Prerequisites
- Python 3.11 or higher
- Git

### 2. Clone Repository
```bash
git clone <repo-url>
cd Campus_Sync
```

### 3. Create & Activate Virtual Environment
```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables
Copy the template configuration:
```bash
# Windows
copy .env.example .env

# Linux / macOS
cp .env.example .env
```

---

## 🔑 Environment Variables

Configured in `.env`:

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `FLASK_ENV` | `development` | Environment mode (`development`, `testing`, `production`) |
| `FLASK_DEBUG` | `true` | Enable hot-reloading in development |
| `FLASK_HOST` | `127.0.0.1` | Local bind address |
| `FLASK_PORT` | `5000` | Port for local server |
| `SECRET_KEY` | `dev-secret-key-for-local-only` | Secret key for signed session cookies |
| `DATABASE_URL` | *(blank)* | PostgreSQL connection URI (falls back to SQLite if empty) |
| `SQLITE_DB_PATH` | `campus_sync.db` | Local SQLite database file |
| `UPLOAD_FOLDER` | `uploads` | Secure directory for student/teacher uploads |
| `MAX_CONTENT_LENGTH_MB` | `16` | Maximum file upload size limit |
| `OPENAI_API_KEY` | *(blank)* | Optional: Remote LLM provider key |
| `GEMINI_API_KEY` | *(blank)* | Optional: Remote Gemini provider key |

---

## 🚀 Running the Application

### Launch Local Server
```bash
python run.py
```
The server will start at:
👉 **http://127.0.0.1:5000**

---

## 👥 Demo Accounts & Credentials

The application includes realistic, pre-seeded academic data:

| Portal Role | Email Address | Password | Account Holder | Sample Records Grounded in DB |
| :--- | :--- | :--- | :--- | :--- |
| **Student** | `student@test.com` | `Student@123` | Alex Johnson | Enrolled in CS Sem 5; 86% attendance; 1 pending fee ($350); 1 pending coursework assignment; scheduled timetable |
| **Student (Peer)** | `riya@test.com` | `Student@123` | Riya Sen | Enrolled in CS Sem 5; 92% attendance; completed fee payments; submission graded |
| **Teacher** | `teacher@test.com` | `Teacher@123` | Dr. Priya Sharma | Teaches CS301 (DBMS), CS302, CS401; 1 pending submission to grade; active quiz; syllabus delivery at 78.6% |
| **Teacher (Peer)**| `teacher2@test.com` | `Teacher@123` | Prof. Rajesh Nair | Teaches CS201 (DSA); peer for lecture replacement coordination |

---

## 🧪 Automated Testing & Verification

Run the full test suite with Pytest:
```bash
pytest -v
```

### Complete Test Results
```
================================ test session starts ================================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0
collected 125 items

tests/test_auth.py (13 tests) ........................... PASSED [ 10%]
tests/test_college_modules.py (23 tests) ................ PASSED [ 28%]
tests/test_copilot.py (40 tests) ........................ PASSED [ 60%]
tests/test_health.py (4 tests) .......................... PASSED [ 63%]
tests/test_phase7_e2e.py (12 tests) ..................... PASSED [ 73%]
tests/test_security_audit.py (16 tests) ................. PASSED [ 86%]
tests/test_ui_modules.py (17 tests) ..................... PASSED [100%]

================================ 125 passed in 152.77s ===============================
```
**Pass Rate: 100% (125 passed out of 125 tests, 0 failed, 0 skipped).**

---

## 🧭 Key Navigation Endpoints

| URL Path | Role Required | Module Description |
| :--- | :--- | :--- |
| `/` | Public | Public landing page with portal highlights |
| `/login` | Public | Authentication page with session fixation defense |
| `/dashboard` | Authenticated | Smart redirect to `/student` or `/teacher` based on role |
| `/student` | Student | Primary student dashboard with smart alerts & statistics |
| `/teacher` | Teacher | Primary teacher dashboard with delivery targets & queues |
| `/copilot` | Authenticated | Dedicated full-screen AI College Copilot workspace |
| `/academics` | Authenticated | Syllabi, attendance logs, coursework, checking, & tests |
| `/exams` | Authenticated | Examination schedules, published results, & fee receipts |
| `/feedback` | Authenticated | Course evaluations and institutional feedback |
| `/settings` | Authenticated | User appearance themes and account preferences |
| `/profile` | Authenticated | Institutional user profile details |
| `/logout` | Authenticated | Session invalidation and redirect to login |
| `/api/health` | Public | Automated health probe (JSON) |
| `/api/status` | Public | Diagnostic service and database status |

---

## 📄 License

MIT License © 2026 Campus_Sync Development Team. Built for Hackathons and Institutional Innovation.
