"""
Campus_Sync – Backend Authorization Decorators

SECURITY RULE: The frontend (Jinja2/JS) is NEVER responsible for enforcing
permissions. These decorators enforce all access control at the Python layer.

Usage:
    @login_required                        # any authenticated user
    @role_required("student")             # students only
    @role_required("teacher")             # teachers only
    @owns_profile("student")             # student accessing their OWN data
"""

import functools
from flask import abort, g
from flask_login import current_user, login_required  # re-export login_required


def role_required(*roles: str):
    """
    Decorator: abort(403) if the logged-in user's role is not in `roles`.
    Must be used AFTER @login_required.
    """
    def decorator(f):
        @functools.wraps(f)
        @login_required
        def wrapper(*args, **kwargs):
            user_role = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
            if user_role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return wrapper
    return decorator


def owns_student_profile(f):
    """
    Decorator: verify the logged-in student owns the profile they are
    requesting by matching the `student_id` URL parameter to their profile.

    Must be used after @login_required + @role_required("student").
    Abort 403 if the student_id in the URL does not belong to current_user.
    """
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        from app.models.student import Student
        sid = kwargs.get("student_id")
        if sid is None:
            abort(400)
        student = Student.query.filter_by(student_id=sid).first_or_404()
        if student.user_id != current_user.id:
            # Student A tried to read Student B's data via URL manipulation
            abort(403)
        g.student = student   # attach to request context for the view to use
        return f(*args, **kwargs)
    return wrapper


def owns_teacher_profile(f):
    """
    Decorator: verify the logged-in teacher owns the profile they are
    requesting. Abort 403 if the teacher_id in the URL does not belong to
    current_user.
    """
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        from app.models.teacher import Teacher
        tid = kwargs.get("teacher_id")
        if tid is None:
            abort(400)
        teacher = Teacher.query.filter_by(teacher_id=tid).first_or_404()
        if teacher.user_id != current_user.id:
            abort(403)
        g.teacher = teacher
        return f(*args, **kwargs)
    return wrapper


# Re-export for convenience
__all__ = [
    "login_required",
    "role_required",
    "owns_student_profile",
    "owns_teacher_profile",
]
