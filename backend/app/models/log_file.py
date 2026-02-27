from datetime import datetime
from app.extensions import db


class LogFile(db.Model):
    __tablename__ = "log_files"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.BigInteger, nullable=False)
    file_type = db.Column(db.String(10), nullable=False)
    entry_count = db.Column(db.Integer, default=0)
    upload_status = db.Column(db.String(20), default="processing")
    analysis_status = db.Column(db.String(20), default="pending")
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    entries = db.relationship(
        "LogEntry", backref="log_file", lazy="dynamic", cascade="all, delete-orphan"
    )
    analysis_results = db.relationship(
        "AnalysisResult", backref="log_file", lazy="dynamic", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "original_filename": self.original_filename,
            "file_size": self.file_size,
            "file_type": self.file_type,
            "entry_count": self.entry_count,
            "upload_status": self.upload_status,
            "analysis_status": self.analysis_status,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
        }
