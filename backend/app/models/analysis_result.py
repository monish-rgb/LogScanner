from datetime import datetime
from app.extensions import db


class AnalysisResult(db.Model):
    __tablename__ = "analysis_results"

    id = db.Column(db.Integer, primary_key=True)
    log_file_id = db.Column(db.Integer, db.ForeignKey("log_files.id"), nullable=False, index=True)
    log_entry_id = db.Column(db.Integer, db.ForeignKey("log_entries.id"), nullable=True, index=True)
    anomaly_type = db.Column(db.String(100), nullable=False)
    confidence_score = db.Column(db.Float, nullable=False)
    explanation = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    log_entry = db.relationship("LogEntry", backref="analysis_results")

    def to_dict(self):
        result = {
            "id": self.id,
            "log_file_id": self.log_file_id,
            "log_entry_id": self.log_entry_id,
            "anomaly_type": self.anomaly_type,
            "confidence_score": self.confidence_score,
            "explanation": self.explanation,
            "severity": self.severity,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if self.log_entry:
            result["log_entry"] = self.log_entry.to_dict()
        return result
