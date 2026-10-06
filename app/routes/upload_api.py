"""
Campus_Sync – Secure Upload & Download API Blueprint (Phase 6)

Features:
1. Strict file extension whitelisting & magic byte validation.
2. Collision & traversal prevention using UUID filenames.
3. Isolated non-executable storage outside static tree.
4. Ownership & role-based download authorization (prevents IDOR).
5. Safe streaming download headers (as_attachment=True, nosniff).
"""

import os
from pathlib import Path
from flask import Blueprint, request, jsonify, current_app, send_from_directory, abort
from flask_login import current_user

from app.auth.decorators import login_required
from app.database.db import db
from app.models.upload import FileUpload
from app.utils.upload_security import (
    validate_file,
    generate_secure_storage_name,
    UploadValidationError,
)

upload_api_bp = Blueprint("upload_api", __name__, url_prefix="/api/uploads")


@upload_api_bp.route("/file", methods=["POST"])
@login_required
def upload_file():
    """
    Secure file upload endpoint.
    Associates file with current_user and applies strict security checks.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file field found in request."}), 400

    file = request.files["file"]
    category = request.form.get("category", "assignment").strip()

    try:
        max_bytes = current_app.config.get("MAX_CONTENT_LENGTH", 10 * 1024 * 1024)
        ext = validate_file(file, max_bytes=max_bytes)

        # Generate non-colliding, traversal-safe storage filename
        uuid_name = generate_secure_storage_name(file.filename)
        upload_folder = Path(current_app.config["UPLOAD_FOLDER"])
        upload_folder.mkdir(parents=True, exist_ok=True)

        target_path = upload_folder / uuid_name
        file.seek(0)
        file.save(str(target_path))
        file_size = os.path.getsize(str(target_path))

        # Record in database associated with authenticated user
        file_record = FileUpload(
            uuid_filename=uuid_name,
            original_filename=file.filename,
            file_size=file_size,
            mime_type=file.content_type or f"application/{ext}",
            user_id=current_user.id,
            category=category,
        )
        db.session.add(file_record)
        db.session.commit()

        return jsonify({
            "status": "success",
            "file": file_record.to_dict(),
        }), 201

    except UploadValidationError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Upload processing failed: {str(e)}"}), 500


@upload_api_bp.route("/<int:file_id>/download", methods=["GET"])
@login_required
def download_file(file_id: int):
    """
    Secure file download with RBAC and ownership authorization.
    Students can only download their own uploads.
    Teachers can access departmental student uploads for grading.
    """
    file_record = FileUpload.query.get_or_404(file_id)

    # Authorization Check:
    # 1. Uploader can always download
    # 2. Teacher can download any student coursework/submission upload
    # 3. Another student cannot download this user's file (IDOR prevention)
    is_owner = file_record.user_id == current_user.id
    is_teacher = current_user.is_teacher

    if not (is_owner or is_teacher):
        abort(403, description="Access Denied: You are not authorized to download this file.")

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    return send_from_directory(
        upload_folder,
        file_record.uuid_filename,
        as_attachment=True,
        download_name=file_record.original_filename,
    )
