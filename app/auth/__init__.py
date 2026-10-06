"""Auth package – exports decorators for use throughout the app."""
from .decorators import login_required, role_required, owns_student_profile, owns_teacher_profile

__all__ = ["login_required", "role_required", "owns_student_profile", "owns_teacher_profile"]
