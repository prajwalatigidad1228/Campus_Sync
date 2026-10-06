"""
Campus_Sync – Secure File Upload Model (Phase 6)
Tracks ownership, file metadata, MIME type, and storage mapping for all user uploads.
"""

from datetime import datetime, timezone
from app.database.db import db


class FileUpload(db.Model):
    """Secure metadata registry for uploaded course materials and submissions."""

    __tablename__ = "file_uploads"

    id = db.Column(db.Integer, primary_key=True)
    uuid_filename = db.Column(db.String(255), unique=True, nullable=False, index=True)
    original_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    
    # Ownership association
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    category = db.Column(db.String(50), default="assignment", nullable=False)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user = db.relationship("User", backref=db.backref("uploaded_files", lazy="dynamic"))

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.original_filename,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "category": self.category,
            "uploader_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "download_url": f"/api/uploads/{self.id}/download",
        }
