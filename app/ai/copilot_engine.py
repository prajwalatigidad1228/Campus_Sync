"""
Campus_Sync – AI Copilot Central Orchestrator (Phase 5)

Architecture:
User -> Authentication -> Identify Role -> Intent Determination -> [Policy: RAG | Data: RBAC Check -> Tool] -> AI Model -> Answer
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from app.models.user import User
from app.ai.guardrails import CopilotGuardrails
from app.ai.tools import (
    StudentCopilotTools,
    TeacherCopilotTools,
    KnowledgeTools,
    ToolAccessDeniedError,
)
from app.ai.rag_engine import rag_engine
from app.ai.llm_service import get_llm_provider, FALLBACK_MESSAGE


def extract_subject_code(query: str) -> Optional[str]:
    """
    Extracts a course/subject code like CS301, CS201, IT101 from query text.
    """
    match = re.search(r'\b([A-Za-z]{2,4}\d{3})\b', query)
    if match:
        return match.group(1).upper()
    return None


def is_policy_question(query: str) -> bool:
    """
    Determines if a query is asking for institutional policies, regulations,
    condonation criteria, examination conduct, or academic calendar rules.
    """
    q_lower = query.lower().strip()

    # Explicit regulatory and policy phrases
    policy_phrases = [
        "minimum attendance",
        "attendance requirement",
        "attendance requirements",
        "attendance rule",
        "attendance rules",
        "attendance policy",
        "attendance criteria",
        "attendance cutoff",
        "percentage attendance is required",
        "attendance is required",
        "attendance needed",
        "attendance necessary",
        "mandatory attendance",
        "condonation policy",
        "condonation rules",
        "condonation",
        "condone",
        "condoned",
        "detention policy",
        "detention rules",
        "detention",
        "below 75",
        "75 percent",
        "75%",
        "hall ticket rule",
        "hall ticket rules",
        "calculator rule",
        "calculator rules",
        "calculators allowed",
        "examination conduct",
        "exam conduct",
        "exam rules",
        "academic calendar",
        "faculty guidelines",
        "replacement regulations",
        "lecture replacement regulations",
        "code of conduct",
        "statute",
        "handbook",
    ]
    if any(phrase in q_lower for phrase in policy_phrases):
        return True

    # Check for general institutional regulatory keywords
    regulatory_keywords = [
        "policy", "policies",
        "regulation", "regulations",
        "criteria", "cutoff", "mandatory",
        "eligibility", "statute",
    ]
    if any(w in q_lower for w in regulatory_keywords):
        return True

    # If asking "what are the rules"
    if "rule" in q_lower or "rules" in q_lower:
        return True

    return False


class CopilotEngine:

    @classmethod
    def chat(
        cls,
        user: User,
        query: str,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Main Copilot chat endpoint logic.

        Returns:
            dict containing:
                "response": str,
                "source": Optional[str],
                "role": str
        """
        history = history or []
        user_role = user.role.value if hasattr(user.role, "value") else str(user.role)
        user_name = user.display_name

        # ── 1. Security & Prompt Injection Pre-Screening ───────────────────
        is_allowed, denial_reason = CopilotGuardrails.screen_query(query, user_role)
        if not is_allowed:
            return {
                "response": denial_reason,
                "source": "Institute Security & Privacy Policy",
                "role": "assistant",
                "is_denied": True,
            }

        q_lower = query.lower().strip()
        context_data = None
        rag_chunks = []

        # ── 2. Determine Intent: Policy Question vs Data Question ───────────
        if is_policy_question(query):
            # ── POLICY / RAG INTENT ─────────────────────────────────────────
            # Route to institutional RAG knowledge base
            rag_chunks = rag_engine.retrieve(query, user_role, top_k=2)
            llm = get_llm_provider()
            answer, source = llm.generate_response(
                user_role=user_role,
                user_name=user_name,
                query=query,
                context_data=None,
                rag_chunks=rag_chunks,
                history=history,
            )
            return {
                "response": answer,
                "source": source,
                "role": "assistant",
                "is_denied": False,
            }

        # ── 3. DATA QUESTION: Resource Identification & RBAC Authorization ─
        try:
            subj_code = extract_subject_code(query)

            if user.is_teacher and user.teacher_profile:
                teacher = user.teacher_profile
                assigned_map = {s.code.upper(): s for s in teacher.subjects}

                # Teacher Smart Alerts / Priorities
                if any(w in q_lower for w in ["focus", "attention", "alert", "priority", "what should i do", "what to do today", "tasks today", "urgent", "todo", "action item", "pending tasks", "remind me"]):
                    context_data = TeacherCopilotTools.get_my_alerts(teacher)

                # Teacher Class Attendance Data Query
                elif "attendance" in q_lower:
                    # Authorization check MUST happen before data access
                    if subj_code and subj_code.upper() not in assigned_map:
                        return {
                            "response": (
                                f"Access Denied: You are not authorized to view attendance for subject '{subj_code}'. "
                                f"You only teach: {', '.join(assigned_map.keys())}."
                            ),
                            "source": "Role Authorization Enforcer",
                            "role": "assistant",
                            "is_denied": True,
                        }
                    context_data = TeacherCopilotTools.get_authorized_class_attendance(teacher, subj_code)

                # Teacher Class Results / Grade Rosters
                elif any(w in q_lower for w in ["result", "results", "marks", "grade", "grades", "score", "scores"]):
                    if subj_code and subj_code.upper() not in assigned_map:
                        return {
                            "response": f"Access Denied: You are not authorized to view results for '{subj_code}'.",
                            "source": "Role Authorization Enforcer",
                            "role": "assistant",
                            "is_denied": True,
                        }
                    context_data = TeacherCopilotTools.get_authorized_class_results(teacher, subj_code)

                # Teacher Assignments
                elif "assignment" in q_lower or "checking" in q_lower or "grading" in q_lower:
                    context_data = TeacherCopilotTools.get_my_assignments(teacher)

                # Teacher Syllabus Targets
                elif "target" in q_lower or "milestone" in q_lower or "hour" in q_lower:
                    context_data = TeacherCopilotTools.get_my_targets(teacher)

                # Teacher Handled Subjects
                elif "subject" in q_lower or "teach" in q_lower:
                    context_data = TeacherCopilotTools.get_my_subjects(teacher)

                # Teacher Replacement Requests
                elif "replacement" in q_lower or "substitute" in q_lower or "swap" in q_lower:
                    context_data = TeacherCopilotTools.get_my_replacement_requests(teacher)

                # Knowledge: Announcements & Syllabus
                elif "announcement" in q_lower or "circular" in q_lower:
                    context_data = KnowledgeTools.search_announcements(user, query)
                elif "syllabus" in q_lower:
                    context_data = KnowledgeTools.search_syllabus(user, subj_code)

            elif user.is_student and user.student_profile:
                student = user.student_profile

                # Student Smart Alerts / Priorities
                if any(w in q_lower for w in ["focus", "attention", "alert", "priority", "what should i do", "what to do today", "tasks today", "urgent", "todo", "action item", "pending tasks", "remind me"]):
                    context_data = StudentCopilotTools.get_my_alerts(student)

                # Student Personal Attendance Data Query
                elif "attendance" in q_lower:
                    context_data = StudentCopilotTools.get_my_attendance(student)

                # Student Personal Assignments
                elif "assignment" in q_lower or "homework" in q_lower or "coursework" in q_lower:
                    context_data = StudentCopilotTools.get_my_assignments(student)

                # Student Personal Results / Grades
                elif any(w in q_lower for w in ["result", "mark", "grade", "score", "sgpa", "cgpa", "marksheet"]):
                    context_data = StudentCopilotTools.get_my_results(student)

                # Student Personal Fees
                elif "fee" in q_lower or "tuition" in q_lower or "invoice" in q_lower or "balance" in q_lower or "receipt" in q_lower:
                    context_data = StudentCopilotTools.get_my_fees(student)

                # Student Upcoming Exams Timetable
                elif ("exam" in q_lower or "timetable" in q_lower) and any(w in q_lower for w in ["my", "when", "schedule", "hall", "date", "upcoming", "next"]):
                    context_data = StudentCopilotTools.get_my_exams(student)

                # Student Online Tests / Quizzes
                elif "quiz" in q_lower or ("test" in q_lower and "exam" not in q_lower):
                    context_data = StudentCopilotTools.get_my_tests(student)

                # Student Profile
                elif "profile" in q_lower or "roll number" in q_lower or "division" in q_lower:
                    context_data = StudentCopilotTools.get_my_profile(student)

                # Knowledge: Announcements & Syllabus
                elif "announcement" in q_lower or "circular" in q_lower or "notice" in q_lower:
                    context_data = KnowledgeTools.search_announcements(user, query)
                elif "syllabus" in q_lower and ("unit" in q_lower or "module" in q_lower or "course" in q_lower):
                    context_data = KnowledgeTools.search_syllabus(user)

        except ToolAccessDeniedError as e:
            return {
                "response": str(e),
                "source": "Role Authorization Enforcer",
                "role": "assistant",
                "is_denied": True,
            }

        # ── 4. Grounded Answer Generation or Mandatory Fallback ─────────────
        # If no database tool was matched (unrelated query like chocolate brownies),
        # retrieve from RAG as a secondary check. Out-of-domain queries return empty chunks.
        if context_data is None:
            rag_chunks = rag_engine.retrieve(query, user_role, top_k=2)

        llm = get_llm_provider()
        answer, source = llm.generate_response(
            user_role=user_role,
            user_name=user_name,
            query=query,
            context_data=context_data,
            rag_chunks=rag_chunks,
            history=history,
        )

        return {
            "response": answer,
            "source": source,
            "role": "assistant",
            "is_denied": False,
        }
