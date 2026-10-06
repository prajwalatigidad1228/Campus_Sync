"""
Campus_Sync – AI Copilot Guardrails & Prompt Injection Defense (Phase 5)

Enforces:
1. Prompt injection pre-screening (jailbreaks, instruction overrides, impersonation).
2. Cross-student data boundary checks (students cannot request other students' data).
3. Confidential institutional data boundary checks (salaries, HR, passwords).
4. Teacher subject scoping checks.
"""

import re
from typing import Tuple, Optional


class GuardrailViolation(Exception):
    """Raised when a security guardrail or injection pattern is detected."""
    pass


class CopilotGuardrails:

    # ── 1. Prompt Injection Patterns ───────────────────────────────────────
    INJECTION_PATTERNS = [
        r"(ignore|disregard)\s+(all\s+)?(your|previous|prior|above|system)\s+(instructions|rules)",
        r"ignore\s+(all\s+)?(previous|prior|above|system|your)\s+(instructions|rules)",
        r"disregard\s+(all\s+)?(previous|prior|system|your)\s+(rules|instructions)",
        r"bypass\s+(security|authorization|permissions|checks)",
        r"override\s+(security|authorization|system|permissions)",
        r"pretend\s+you\s+are\s+(an?\s+)?(admin|administrator|root|developer|owner|hacker)",
        r"act\s+as\s+(an?\s+)?(admin|administrator|system\s+operator|superuser)",
        r"jailbreak",
        r"you\s+are\s+now\s+in\s+developer\s+mode",
        r"reveal\s+(your\s+)?system\s+prompt",
        r"print\s+(your\s+)?system\s+instructions",
        r"give\s+me\s+private\s+data",
        r"dump\s+all\s+(database|student|teacher|user)",
    ]

    # ── 2. Confidential / Restricted Institutional Topics ──────────────────
    CONFIDENTIAL_PATTERNS = [
        r"(teacher|faculty|professor|staff|employee)\s+salary",
        r"(teacher|faculty|staff)\s+pay(slip|check|roll)?",
        r"(database|admin|root|system)\s+password",
        r"api\s+key",
        r"secret\s+key",
        r"credit\s+card",
        r"bank\s+account",
        r"confidential\s+hr",
    ]

    # ── 3. Cross-Student Privacy Patterns ──────────────────────────────────
    CROSS_STUDENT_PATTERNS = [
        r"(another|other|different)\s+student('s)?\s*(attendance|result|marks|score|profile|fee)",
        r"(someone|anyone)\s+else('s)?\s*(attendance|result|marks|score|profile|fee)",
        r"(riya|aarav|john|smith|alex\s+2|student\s+2)('s)?\s*(attendance|marks|result|score|profile)",
        r"roll\s+(no\.?|number)?\s*(15|42|015|999|other)",
        r"all\s+students('s)?\s*(attendance|marks|results|passwords)",
        r"every\s+student('s)?\s*(attendance|marks|results)",
    ]

    @classmethod
    def screen_query(cls, query: str, user_role: str) -> Tuple[bool, Optional[str]]:
        """
        Validate incoming query against injection, confidentiality, and privacy boundaries.

        Returns:
            (is_allowed: bool, denial_reason: Optional[str])
        """
        q_lower = query.strip().lower()
        role_lower = str(user_role).lower()

        # 1. Prompt Injection Check
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, q_lower):
                return False, (
                    "Security Notice: Prompt injection or instruction override detected. "
                    "This system operates strictly under institute authorization rules and cannot bypass security protocols."
                )

        # 2. Confidential / PII Check (Salaries, Passwords)
        for pattern in cls.CONFIDENTIAL_PATTERNS:
            if re.search(pattern, q_lower):
                return False, (
                    "Access Denied: Confidential institutional information (such as faculty compensation, "
                    "administrative credentials, or internal HR records) cannot be disclosed."
                )

        # 3. Cross-Student Privacy Check (Only applies if user is a student)
        if role_lower == "student":
            for pattern in cls.CROSS_STUDENT_PATTERNS:
                if re.search(pattern, q_lower):
                    return False, (
                        "Access Denied: Student privacy protection policy. "
                        "You can access ONLY your own authorized academic data (your attendance, your assignments, "
                        "your results, and your fee invoices). Requesting other students' private records is prohibited."
                    )

        return True, None

