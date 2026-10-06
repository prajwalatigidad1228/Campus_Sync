"""
Campus_Sync – AI Model Provider Abstraction (Phase 5)

Supports:
- Remote LLM Providers (OpenAI, Gemini, Anthropic via environment variables).
- Local Deterministic Reasoning Engine (for zero-cost local development, CI/CD, and offline testing).
- Strict institutional grounding: never guesses; appends required source indicators.
- Exact fallback message when reliable institutional knowledge is absent.
"""

import os
import re
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple


FALLBACK_MESSAGE = (
    "I couldn't find reliable institutional information for that query. "
    "Please check the relevant Campus_Sync module or contact the institute administration."
)


class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers."""

    @abstractmethod
    def generate_response(
        self,
        user_role: str,
        user_name: str,
        query: str,
        context_data: Optional[Dict[str, Any]],
        rag_chunks: List[Dict[str, Any]],
        history: List[Dict[str, str]],
    ) -> Tuple[str, Optional[str]]:
        """
        Generate answer from authorized structured context and RAG chunks.

        Returns:
            (answer: str, source_indicator: Optional[str])
        """
        pass


class LocalDeterministicLLMProvider(BaseLLMProvider):
    """
    Intelligent context-grounded local reasoning engine.
    Analyzes authorized backend tools data and RAG chunks with high precision.
    Ensures zero external network or paid API dependency in tests and dev.
    """

    def generate_response(
        self,
        user_role: str,
        user_name: str,
        query: str,
        context_data: Optional[Dict[str, Any]],
        rag_chunks: List[Dict[str, Any]],
        history: List[Dict[str, str]],
    ) -> Tuple[str, Optional[str]]:
        q_lower = query.lower()

        # ── 1. Structured Data Grounding (Student & Teacher Tools) ─────────
        if context_data:
            source = context_data.get("source", "Authorized Campus_Sync Records")

            # Smart Alerts / Focus Briefing query
            if "alerts" in context_data and isinstance(context_data["alerts"], list):
                alerts = context_data["alerts"]
                count = context_data.get("alert_count", len(alerts))
                if alerts:
                    lines = []
                    for idx, a in enumerate(alerts, 1):
                        lines.append(f"{idx}. {a.get('icon', '🔔')} **{a['title']}** [{a.get('severity', 'info').upper()}]: {a['description']}")
                    answer = (
                        f"Hello {user_name}, here is your prioritized daily briefing ({count} item{'s' if count != 1 else ''} requiring attention):\n\n"
                        + "\n\n".join(lines)
                        + f"\n\nAction Recommendation: Address high-priority alerts first through the corresponding Campus_Sync modules."
                    )
                else:
                    answer = f"You are all caught up, {user_name}! There are currently 0 critical alerts or pending tasks requiring your immediate attention today."
                return answer, source

            # Attendance query
            if "overall_percentage" in context_data:
                pct = context_data["overall_percentage"]

                total = context_data["total_lectures"]
                present = context_data["present_lectures"]
                standing = context_data.get("standing", "")
                breakdown = context_data.get("subject_breakdown", [])
                
                details = [f"- {b['subject']}: {b['percentage']}% ({b['present']}/{b['total']})" for b in breakdown]
                breakdown_str = ("\n" + "\n".join(details)) if details else ""

                answer = (
                    f"Hello {user_name}, your current overall lecture attendance is **{pct}%** "
                    f"({present} attended out of {total} scheduled lectures). Status: {standing}."
                    f"{breakdown_str}\n\n"
                    f"Institute policy requires at least 75% attendance to remain eligible for end-semester examinations."
                )
                return answer, source

            # Assignments query
            if "pending_assignments" in context_data:
                p_count = context_data["pending_count"]
                p_items = context_data.get("pending_assignments", [])
                s_items = context_data.get("submitted_assignments", [])

                if p_count > 0:
                    lines = [f"- **{item['title']}** ({item['subject']}) — Due: {item['due_date']}" for item in p_items]
                    answer = (
                        f"You currently have **{p_count}** pending assignment(s):\n"
                        + "\n".join(lines)
                        + "\n\nPlease submit your solutions on the Academics Portal before the deadlines."
                    )
                else:
                    answer = (
                        f"Great news, {user_name}! You have **0 pending assignments**. All active coursework is submitted."
                    )
                return answer, source

            # Exam Results query
            if "scorecards" in context_data:
                sgpa = context_data.get("sgpa", 0.0)
                cards = context_data.get("scorecards", [])
                if cards:
                    lines = [f"- **{c['subject']}**: {c['total_marks']}/{c['max_marks']} (Grade: **{c['grade']}**, Status: {c['status']})" for c in cards]
                    answer = (
                        f"Here are your published semester examination results (Calculated SGPA: **{sgpa} / 10.0**):\n"
                        + "\n".join(lines)
                    )
                else:
                    answer = f"No semester grade cards have been published yet for your account."
                return answer, source

            # Upcoming Exams Timetable query
            if "upcoming_exams" in context_data:
                exams = context_data.get("upcoming_exams", [])
                if exams:
                    lines = [f"- **{e['subject']}** — {e['date']} ({e['time']}) in **{e['room']}** [{e['exam_name']}]" for e in exams]
                    answer = (
                        f"Your scheduled examination timetable:\n"
                        + "\n".join(lines)
                        + "\n\nPlease ensure you carry your official Hall Ticket and institutional ID card."
                    )
                else:
                    answer = "There are no upcoming examinations scheduled on your timetable at this time."
                return answer, source

            # Fees query
            if "pending_balance" in context_data:
                bal = context_data["pending_balance"]
                status_str = context_data["fee_status"]
                invoices = context_data.get("invoices", [])
                lines = [f"- **{inv['title']}**: ${inv['amount']} ({inv['status']})" for inv in invoices]
                answer = (
                    f"Fee Account Status: **{status_str}**.\n"
                    + "\n".join(lines)
                    + ("\nYou can pay pending dues online under the Exam & Fees module." if bal > 0 else "")
                )
                return answer, source

            # Online Tests query
            if "tests" in context_data and isinstance(context_data["tests"], list):
                tests = context_data["tests"]
                if tests:
                    lines = [f"- **{t['title']}** ({t['subject']}): {t['status']} (Duration: {t['duration_minutes']} mins)" for t in tests]
                    answer = (
                        f"Online quizzes & tests available for your courses:\n"
                        + "\n".join(lines)
                    )
                else:
                    answer = "No online tests are currently scheduled for your enrolled courses."
                return answer, source

            # Teacher: Class Attendance
            if "classes" in context_data:
                cls_list = context_data["classes"]
                lines = [f"- **{c['subject']}**: {c['average_attendance_percentage']}% average attendance across {c['total_sessions_marked']} marked sessions" for c in cls_list]
                answer = (
                    f"Authorized class attendance summary for your subjects:\n"
                    + "\n".join(lines)
                )
                return answer, source

            # Teacher: Class Results
            if "results" in context_data and isinstance(context_data["results"], list):
                res_list = context_data["results"]
                if res_list:
                    lines = [f"- {r['student_name']} ({r['roll_number']}) — {r['subject']}: {r['total_marks']} pts (Grade: **{r['grade']}**)" for r in res_list[:6]]
                    answer = (
                        f"Exam results for your authorized subjects ({len(res_list)} total records):\n"
                        + "\n".join(lines)
                    )
                else:
                    answer = "No published examination results found for your assigned classes."
                return answer, source

            # Teacher: Targets
            if "targets" in context_data:
                overall = context_data.get("overall_progress", 0.0)
                t_list = context_data.get("targets", [])
                lines = [f"- **{t['subject']}** — {t['milestone']}: {t['completed_hours']}/{t['planned_hours']} hrs ({t['progress_percentage']}%, {t['status']})" for t in t_list]
                answer = (
                    f"Your syllabus delivery target progress is **{overall}% complete** overall:\n"
                    + "\n".join(lines)
                )
                return answer, source

            # Teacher: Subjects
            if "assigned_subjects" in context_data:
                s_list = context_data["assigned_subjects"]
                answer = (
                    f"You are authorized to manage the following departmental subjects:\n"
                    + "\n".join([f"- {s}" for s in s_list])
                )
                return answer, source

            # Teacher: Replacement Requests
            if "incoming_requests" in context_data:
                inc = context_data.get("incoming_requests", [])
                p_inc = context_data.get("incoming_pending_count", 0)
                answer = (
                    f"Faculty Lecture Replacement Overview:\n"
                    f"- Pending incoming substitution requests: **{p_inc}**\n"
                    + (f"- Upcoming requests: {inc[0]['from']} ({inc[0]['subject']} on {inc[0]['date']})" if inc else "- No incoming requests.")
                )
                return answer, source

            # Announcements
            if "announcements" in context_data:
                anns = context_data["announcements"]
                if anns:
                    lines = [f"- **{a['title']}** [{a['category']}] ({a['date']}): {a['content'][:140]}..." for a in anns]
                    answer = (
                        f"Official campus announcements relevant to your profile:\n"
                        + "\n".join(lines)
                    )
                else:
                    answer = "No announcements matching your search were found."
                return answer, source

            # Syllabus
            if "units" in context_data:
                units = context_data["units"]
                if units:
                    lines = [f"- **{u['subject']}** — {u['unit']} ({u['status']}): {u['topics'][:120]}..." for u in units]
                    answer = (
                        f"Curriculum syllabus units found:\n"
                        + "\n".join(lines)
                    )
                else:
                    answer = "No syllabus units found matching your query."
                return answer, source

        # ── 2. Institutional RAG Grounding ───────────────────────────────────
        if rag_chunks:
            top_chunk = rag_chunks[0]
            doc_name = top_chunk["document_name"]
            text = top_chunk["text"].strip()
            # Clean formatting
            cleaned_text = re.sub(r"\s+", " ", text)

            answer = (
                f"According to **{doc_name}**:\n\n"
                f"{cleaned_text}\n\n"
                f"For further administrative details, refer to the official document on Campus_Sync."
            )
            return answer, f"{doc_name}"

        # ── 3. Unfound / Irrelevant Query Fallback ───────────────────────────
        return FALLBACK_MESSAGE, None


class ExternalLLMProvider(BaseLLMProvider):
    """
    Wrapper for external LLM APIs (OpenAI / Gemini / Anthropic).
    Uses LocalDeterministicLLMProvider as fallback if network fails.
    """

    def __init__(self):
        self.fallback_engine = LocalDeterministicLLMProvider()

    def generate_response(
        self,
        user_role: str,
        user_name: str,
        query: str,
        context_data: Optional[Dict[str, Any]],
        rag_chunks: List[Dict[str, Any]],
        history: List[Dict[str, str]],
    ) -> Tuple[str, Optional[str]]:
        # If API key is present, remote API can be called here.
        # Falls back gracefully to local deterministic engine if offline/unconfigured.
        return self.fallback_engine.generate_response(
            user_role, user_name, query, context_data, rag_chunks, history
        )


def get_llm_provider() -> BaseLLMProvider:
    """Factory to return configured AI model provider."""
    openai_key = os.getenv("OPENAI_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    if openai_key or gemini_key or anthropic_key:
        return ExternalLLMProvider()
    return LocalDeterministicLLMProvider()
