# Campus_Sync — Security Architecture & Threat Defense Specification

Campus_Sync implements an enterprise-grade, defense-in-depth security model engineered to protect student privacy, faculty coursework, and institutional data integrity.

---

## 1. Authentication & Session Management

- **Password Hashing**: Passwords are cryptographically hashed using **Bcrypt** with salted rounds via `flask-bcrypt`. Plaintext passwords are never stored, logged, or exposed.
- **Session Fixation Defense**: Pre-existing session state and tokens are explicitly cleared (`session.clear()`) upon both login and logout to eliminate session fixation vectors.
- **Cookie Hardening**:
  - `SESSION_COOKIE_HTTPONLY = True`: Blocks client-side script access to authentication cookies, mitigating cookie theft via XSS.
  - `SESSION_COOKIE_SAMESITE = 'Lax'`: Mitigates Cross-Site Request Forgery (CSRF) across top-level cross-site navigations.
  - `SESSION_COOKIE_SECURE = True`: Automatically enforced in production environments over HTTPS.
- **Open Redirect Protection**: Login redirects inspect the target parameter, rejecting protocol-relative URLs (`//evil.com`) and path escapes (`\`).

---

## 2. Role-Based Access Control (RBAC) & Boundary Isolation

Campus_Sync operates with **strictly two primary roles**:
1. **Student**
2. **Teacher**

- **Zero Role Mixing**: Permissions are verified at the backend API and controller layer via `@login_required` and `@role_required("<role>")` decorators. Client-side navigation visibility is never relied upon as an authorization boundary.
- **Insecure Direct Object Reference (IDOR) Protections**:
  - **Fees**: A student can only view and pay fees belonging to their authenticated profile (`fee.student_id == current_user.student_profile.id`). Cross-student invoice payment is denied with `403 Forbidden`.
  - **Grades & Submissions**: Students can only access their own coursework submissions. Only teachers explicitly assigned to the parent course subject can view, evaluate, and award marks.
  - **Class Registers**: Teachers can mark and inspect attendance only for subjects assigned to them in the institutional course directory (`teacher.teaches_subject()`). Unauthorized subjects raise `AuthorizationError` / `403 Forbidden`.
  - **Profiles**: Profile routes (`/student/profile/<id>`, `/teacher/profile/<id>`) enforce ownership decorators (`@owns_student_profile`, `@owns_teacher_profile`). Accessing another user's profile URI results in immediate HTTP 403.

---

## 3. Secure File Upload Pipeline

File uploads are protected by a dedicated validation and sandboxing engine in [`app/utils/upload_security.py`](file:///c:/Users/Pranav/OneDrive/Desktop/Campus_Sync/app/utils/upload_security.py):

- **Strict Extension Whitelist**: Permitted formats are limited to `.pdf`, `.png`, `.jpg`, `.jpeg`, `.txt`, `.docx`, and `.zip`.
- **Executable Blacklist**: Dangerous extensions (`.exe`, `.py`, `.sh`, `.bat`, `.php`, `.js`, `.html`, `.dll`) are categorically rejected.
- **Magic Byte Signature Inspection**: Binary file headers are inspected against known file signatures (e.g. `%PDF-`, `\x89PNG`, `\xff\xd8\xff`, `PK\x03\x04`). Executable or script files disguised with safe extensions are rejected with `UploadValidationError`.
- **Path Traversal Defense**: Filenames are sanitized with `secure_filename()` and prepended with a cryptographically unique `UUID4` hex string. Files cannot overwrite existing assets or escape into parent directories (`../`).
- **Execution Prevention**: Files are saved in an isolated directory (`uploads/`) outside the static web tree. Files cannot be executed by the web server.
- **Authorized Streaming Downloads**: Download route (`/api/uploads/<id>/download`) checks that the requester is the original uploader or an authorized course teacher. Downloads are streamed with `as_attachment=True` and `X-Content-Type-Options: nosniff`.

---

## 4. AI Copilot & Institutional RAG Security

The Campus_Sync AI Copilot enforces the **Authorization-First Architecture**:

```
User Query
    ↓
Authentication & Role Identification
    ↓
Security Pre-Screening (CopilotGuardrails)
    ↓
Role-Scoped Tool Execution / Filtered RAG Search
    ↓
AI Reasoning Engine (Provider Abstraction)
    ↓
Grounded Output + Mandatory Source Attribution
```

- **Zero Arbitrary SQL Execution**: The Copilot is architecturally prohibited from generating or executing arbitrary SQL queries. All data access occurs via predefined Python functions returning bounded data models.
- **Prompt Injection Defense**: [`CopilotGuardrails`](file:///c:/Users/Pranav/OneDrive/Desktop/Campus_Sync/app/ai/guardrails.py) detects and blocks instruction override attempts (e.g., *"Ignore previous instructions"*, *"System override"*, *"Jailbreak developer mode"*) before any tool or retrieval executes.
- **Cross-Student Privacy**: Students requesting peer information (e.g., *"What is Riya's marks?"*, *"Show roll 15 attendance"*) are intercepted and rejected with a student privacy violation notice.
- **Teacher Course Scoping**: Faculty queries for unassigned course results or attendance raise `ToolAccessDeniedError`.
- **Confidential Data Defense**: Queries regarding faculty compensation, administrator credentials, or system passwords are systematically denied.
- **RAG Access-Scope Filtering**: Institutional document chunks carry an `access_scope` attribute (`"all"`, `"student"`, or `"teacher"`). Student queries cannot retrieve teacher-only policy guidelines.
- **Mandatory Institutional Fallback**: Out-of-domain or ungrounded questions return the exact required message:
  > *"I couldn't find reliable institutional information for that query. Please check the relevant Campus_Sync module or contact the institute administration."*

---

## 5. Injection Defenses & HTTP Security Headers

- **SQL Injection Defense**: 100% of database interactions utilize SQLAlchemy ORM parameterized queries. Raw string concatenation in queries is strictly avoided.
- **Cross-Site Scripting (XSS)**: Jinja2 templates utilize contextual auto-escaping by default.
- **HTTP Security Headers**: Every HTTP response carries OWASP-recommended defensive headers via [`app/utils/security_headers.py`](file:///c:/Users/Pranav/OneDrive/Desktop/Campus_Sync/app/utils/security_headers.py):
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: SAMEORIGIN`
  - `X-XSS-Protection: 1; mode=block`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Content-Security-Policy: default-src 'self' ...`
- **CORS Protection**: Restricted to authorized origins rather than wildcard origins in production environments.
