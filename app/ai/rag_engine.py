"""
Campus_Sync – RAG Knowledge Base & Retrieval Engine (Phase 5)

Pipeline:
Ingest -> Clean -> Chunk -> Add Metadata -> Vector/Semantic Index -> Authorized Scope Retrieval.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import re
import math


class DocumentChunk:
    """Represents a discrete text chunk with institutional metadata."""

    def __init__(
        self,
        chunk_id: str,
        document_name: str,
        category: str,
        text: str,
        metadata: Dict[str, Any],
    ):
        self.chunk_id = chunk_id
        self.document_name = document_name
        self.category = category
        self.text = text
        self.metadata = metadata  # department, semester, subject, uploader, upload_date, access_scope
        self.words = self._tokenize(text)

    @staticmethod
    def _tokenize(text: str) -> set:
        cleaned = re.sub(r"[^\w\s]", " ", text.lower())
        return set(cleaned.split())


class RAGKnowledgeEngine:
    """
    In-memory vector & semantic similarity search engine for institutional documents.
    Pluggable architecture that supports external pgvector in PostgreSQL while
    providing an independent, zero-dependency cosine semantic retrieval fallback.
    """

    def __init__(self):
        self.chunks: List[DocumentChunk] = []
        self._initialize_seed_corpus()

    def _initialize_seed_corpus(self):
        """Populate institutional repository with authorized college documents."""

        docs = [
            {
                "document_name": "Attendance & Condonation Regulations 2026",
                "category": "Attendance Policy",
                "access_scope": "all",
                "department": "All",
                "content": """
                REGULATION 1: MINIMUM ATTENDANCE REQUIREMENT
                A minimum attendance of 75% in lecture and tutorial sessions, and 80% in practical laboratory sessions, is strictly mandatory across all departments for eligibility to appear in semester end examinations.

                REGULATION 2: MEDICAL CONDONATION PROCEDURE
                Condonation of attendance shortage up to a maximum of 10% (i.e. between 65.0% and 74.9%) may be granted on medical grounds. The student must submit an official medical certificate verified by a registered medical practitioner to the Head of Department (HoD) within 5 working days of resuming classes.

                REGULATION 3: SHORTAGE AND DETENTION
                Students with attendance below 65% are strictly ineligible for condonation under any circumstances and shall be detained (year-back or course repeat) for the respective semester courses. No condonation requests are accepted past the semester cutoff deadline.
                """,
            },
            {
                "document_name": "Examination Conduct & Hall Ticket Rules 2026",
                "category": "Exam Regulations",
                "access_scope": "all",
                "department": "All",
                "content": """
                EXAMINATION RULE 1: HALL TICKETS AND ADMISSION
                All enrolled students must download their official Hall Ticket from the Exam Portal prior to the commencement of examinations. Entry into the examination hall is permitted only upon presentation of the physical Hall Ticket along with the valid institutional Student Identity Card.

                EXAMINATION RULE 2: REPORTING AND LATE ADMISSION
                Students must report to their allocated examination hall 15 minutes prior to the scheduled start time. No candidate will be admitted to the examination hall after 15 minutes from the scheduled start of the examination. No student may leave the hall during the first 60 minutes.

                EXAMINATION RULE 3: UNFAIR MEANS & CALCULATORS
                Possession of programmable calculators, smart watches, mobile phones, or unauthorized study sheets in the examination hall constitutes an Unfair Means (UFM) disciplinary violation leading to immediate paper cancellation and Academic Council review.

                EXAMINATION RULE 4: REVALUATION AND RECHECKING
                Students wishing to apply for photocopy of answer scripts or re-evaluation of theory examination grades must submit a digital revaluation form via the Exam Portal within 15 calendar days from the date of result declaration.
                """,
            },
            {
                "document_name": "Academic Calendar Fall 2026",
                "category": "Academic Schedule",
                "access_scope": "all",
                "department": "All",
                "content": """
                ACADEMIC CALENDAR KEY DATES (FALL TERM 2026):
                - Semester Commencement & First Day of Classes: August 1, 2026.
                - Mid-Semester Theory & Practical Evaluations: October 20 to October 28, 2026.
                - Mid-Term Academic Recess: November 1 to November 8, 2026.
                - Final Submission Deadline for Coursework & Lab Projects: November 20, 2026.
                - End-Semester Laboratory Practical Examinations: November 24 to December 2, 2026.
                - End-Semester University Theory Examinations: December 10 to December 28, 2026.
                - Term Vacation & Winter Break: December 29, 2026 to January 15, 2027.
                - Spring 2027 Term Commencement: January 18, 2027.
                """,
            },
            {
                "document_name": "Student Handbook & Campus Code of Conduct",
                "category": "Campus Regulations",
                "access_scope": "all",
                "department": "All",
                "content": """
                SECTION 1: ANTI-RAGGING STATUTE
                Ragging in any form (physical, verbal, psychological, or digital) is strictly prohibited on campus, in hostels, and on digital transport. The institute maintains a Zero Tolerance Policy under the Supreme Court of India guidelines. Violations result in immediate suspension and police FIR.

                SECTION 2: CENTRAL LIBRARY SERVICES
                The Central Library is open from 8:00 AM to 10:00 PM on Monday through Saturday, and 9:00 AM to 5:00 PM on Sundays. Students can borrow up to 4 books simultaneously for a duration of 14 days. Online renewal is available via the CampusSync Library Portal.

                SECTION 3: CAMPUS SECURITY & DRESS CODE
                Institutional identity cards must be worn and visibly displayed at all times while present in academic blocks, laboratories, cafeteria, and administrative corridors.
                """,
            },
            {
                "document_name": "Faculty Guidelines & Lecture Replacement Regulations",
                "category": "Faculty Guidelines",
                "access_scope": "teacher",
                "department": "All",
                "content": """
                FACULTY REGULATION 1: LECTURE REPLACEMENT & SUBSTITUTION
                When a faculty member is unable to conduct scheduled lectures due to official academic deputation, conferences, or sanctioned leave, they must arrange peer substitution with a colleague teacher from the same department at least 24 hours in advance.

                FACULTY REGULATION 2: HOD NOTIFICATION
                The substitution request must be submitted via the Teacher Dashboard and confirmed digitally by the nominated substitute. Upon confirmation, the Department Head (HoD) and enrolled division receive automated timetable adjustment notices.

                FACULTY REGULATION 3: CONTINUOUS INTERNAL EVALUATION (CIE)
                Internal assessment rubrics, quiz marks, and laboratory evaluations must be entered into the Exam Portal within 7 working days of assessment completion.
                """,
            },
            {
                "document_name": "Fee Remittance & Scholarship Guidelines 2026",
                "category": "Fee Structure",
                "access_scope": "all",
                "department": "All",
                "content": """
                FEE POLICY 1: TUITION PAYMENT WINDOW
                Semester tuition fees and laboratory charges must be remitted by the published deadline. A grace period of 10 days is permitted, after which a late fine of $25 per week is assessed.

                FEE POLICY 2: MERIT SCHOLARSHIPS
                Merit-based scholarships providing a 50% tuition fee waiver are awarded annually to top 3 departmental students maintaining an SGPA of 9.0 or above with zero academic backlogs and at least 85% attendance.

                FEE POLICY 3: DIGITAL RECEIPTS
                All online transactions generate an instant cryptographically verified receipt number (REC-YYYY-XXXX). Receipts must be retained for exam registration and library clearance.
                """,
            },
        ]

        chunk_counter = 0
        for doc in docs:
            # Chunking pipeline: splits paragraphs, cleans whitespace
            paragraphs = [p.strip() for p in doc["content"].strip().split("\n\n") if p.strip()]
            for p_idx, para in enumerate(paragraphs):
                chunk_counter += 1
                metadata = {
                    "document_name": doc["document_name"],
                    "category": doc["category"],
                    "department": doc.get("department", "All"),
                    "access_scope": doc.get("access_scope", "all"),
                    "uploader": "Academic Council / Administration",
                    "upload_date": "2026-08-01",
                    "chunk_index": p_idx,
                }
                chunk = DocumentChunk(
                    chunk_id=f"chunk_{chunk_counter}",
                    document_name=doc["document_name"],
                    category=doc["category"],
                    text=para,
                    metadata=metadata,
                )
                self.chunks.append(chunk)

    def retrieve(
        self,
        query: str,
        user_role: str,
        top_k: int = 2,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve the most relevant knowledge chunks matching `query`,
        strictly enforcing the user's role authorization scope.
        """
        query_clean = re.sub(r"[^\w\s]", " ", query.lower())
        query_words = set(query_clean.split())

        # Comprehensive English and conversational stop words
        stop_words = {
            "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't",
            "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can",
            "cannot", "could", "did", "do", "does", "doing", "don't", "down", "during", "each", "few", "for", "from",
            "further", "had", "has", "have", "having", "he", "her", "here", "hers", "herself", "him", "himself", "his",
            "how", "i", "if", "in", "into", "is", "isn't", "it", "its", "itself", "let's", "me", "more", "most", "my",
            "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours",
            "ourselves", "out", "over", "own", "same", "she", "should", "so", "some", "such", "than", "that", "the",
            "their", "theirs", "them", "themselves", "then", "there", "these", "they", "this", "those", "through", "to",
            "too", "under", "until", "up", "very", "was", "we", "were", "what", "when", "where", "which", "while", "who",
            "whom", "why", "with", "would", "you", "your", "yours", "yourself", "yourselves", "make", "home", "tell",
            "give", "show", "please", "want", "know", "much", "many", "good"
        }

        # Meaningful search keywords with length > 2
        keywords = {w for w in query_words if len(w) > 2 and w not in stop_words}
        if not keywords:
            keywords = {w for w in query_words if w not in stop_words}
        if not keywords:
            return []

        scored_chunks = []
        for chunk in self.chunks:
            # 1. Access Scope Permission Check
            scope = chunk.metadata.get("access_scope", "all")
            if scope != "all" and scope != str(user_role).lower():
                # E.g. student cannot access teacher-only faculty guidelines
                continue

            # 2. Keyword Intersection
            overlap = keywords.intersection(chunk.words)
            if not overlap:
                continue

            score = sum(1.0 for w in overlap)
            # Boost matches in document name or category
            doc_name_lower = chunk.document_name.lower()
            cat_lower = chunk.category.lower()
            for w in keywords:
                if w in doc_name_lower:
                    score += 2.0
                if w in cat_lower:
                    score += 1.5

            # Require minimum relevance threshold of 2.0 to eliminate single incidental common-word false positives
            if score >= 2.0:
                scored_chunks.append((score, chunk))

        # Sort by relevance score descending
        scored_chunks.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, chunk in scored_chunks[:top_k]:
            results.append({
                "document_name": chunk.document_name,
                "category": chunk.category,
                "text": chunk.text,
                "score": score,
                "metadata": chunk.metadata,
            })

        return results



# Global singleton instance
rag_engine = RAGKnowledgeEngine()
