"""
Campus_Sync – Upload Security & Validation Utilities (Phase 6)

Guarantees:
1. Allowed extensions whitelist only (.pdf, .png, .jpg, .jpeg, .txt, .docx, .zip).
2. Hard blacklist of executable code extensions (.exe, .py, .sh, .php, .js, .html).
3. Magic byte signature verification to prevent disguised executable binaries.
4. Path traversal prevention via secure_filename and UUID-based collision prevention.
5. Max file size enforcement.
6. Execution prevention: files stored outside web root and served as attachments.
"""

import os
import uuid
from typing import Tuple, Optional
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "txt", "docx", "zip"}
DISALLOWED_EXTENSIONS = {
    "exe", "py", "sh", "bat", "cmd", "ps1", "php", "phtml",
    "js", "html", "htm", "vbs", "dll", "so", "cgi", "pl", "jar"
}

# Magic byte signatures for authorized file types
MAGIC_SIGNATURES = {
    "pdf": [b"%PDF-"],
    "png": [b"\x89PNG\r\n\x1a\n"],
    "jpg": [b"\xff\xd8\xff"],
    "jpeg": [b"\xff\xd8\xff"],
    "zip": [b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"],
    "docx": [b"PK\x03\x04"],  # DOCX is an OpenXML ZIP archive
}


class UploadValidationError(Exception):
    """Raised when an uploaded file violates safety or type criteria."""
    pass


def get_extension(filename: str) -> str:
    """Extract lowercase file extension without dot."""
    if "." not in filename:
        return ""
    return filename.rsplit(".", 1)[1].lower()


def validate_file(file: FileStorage, max_bytes: int = 10 * 1024 * 1024) -> str:
    """
    Thoroughly validate uploaded file:
    - Non-empty filename
    - Allowed extension whitelist check
    - Disallowed extension blacklist check
    - File size check
    - Magic byte header inspection

    Returns:
        ext: verified extension string
    """
    if not file or not file.filename:
        raise UploadValidationError("No file was selected for upload.")

    orig_name = file.filename.strip()
    ext = get_extension(orig_name)

    if not ext:
        raise UploadValidationError("Files without extensions are not permitted.")

    if ext in DISALLOWED_EXTENSIONS:
        raise UploadValidationError(f"File extension '.{ext}' is strictly prohibited for security reasons.")

    if ext not in ALLOWED_EXTENSIONS:
        raise UploadValidationError(
            f"File extension '.{ext}' is not permitted. Allowed extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}."
        )

    # Read first 512 bytes for magic bytes and size check
    header = file.read(512)
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)  # Reset stream position

    if size == 0:
        raise UploadValidationError("Uploaded file is empty (0 bytes).")

    if size > max_bytes:
        raise UploadValidationError(
            f"File size ({size / (1024*1024):.1f}MB) exceeds the maximum limit of {max_bytes / (1024*1024):.1f}MB."
        )

    # Magic byte validation for binary types
    if ext in MAGIC_SIGNATURES:
        signatures = MAGIC_SIGNATURES[ext]
        has_valid_signature = any(header.startswith(sig) for sig in signatures)
        if not has_valid_signature:
            raise UploadValidationError(
                f"File content does not match genuine .{ext} format (magic byte mismatch). "
                f"Disguised or corrupted files are rejected."
            )
    elif ext == "txt":
        # Ensure plain text does not contain binary NULL bytes (which indicate compiled code)
        if b"\x00" in header:
            raise UploadValidationError("Text files cannot contain binary null bytes.")

    return ext


def generate_secure_storage_name(filename: str) -> str:
    """
    Sanitizes filename and attaches UUID to prevent path traversal and overwrites.
    Example: '../../../hack.pdf' -> 'c3f4e1..._hack.pdf'
    """
    clean_base = secure_filename(filename)
    if not clean_base:
        clean_base = "upload_file"
    unique_id = uuid.uuid4().hex
    return f"{unique_id}_{clean_base}"
