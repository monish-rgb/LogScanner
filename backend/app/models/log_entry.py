from app.extensions import db


class LogEntry(db.Model):
    __tablename__ = "log_entries"

    id = db.Column(db.Integer, primary_key=True)
    log_file_id = db.Column(db.Integer, db.ForeignKey("log_files.id"), nullable=False, index=True)
    line_number = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=True)
    source_ip = db.Column(db.String(45), nullable=True)
    destination_url = db.Column(db.Text, nullable=True)
    user = db.Column(db.String(120), nullable=True)
    action = db.Column(db.String(50), nullable=True)
    category = db.Column(db.String(100), nullable=True)
    risk_score = db.Column(db.Integer, nullable=True)
    bytes_transferred = db.Column(db.BigInteger, nullable=True)
    response_time_ms = db.Column(db.Integer, nullable=True)
    raw_line = db.Column(db.Text, nullable=False)
    is_anomalous = db.Column(db.Boolean, default=False, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "log_file_id": self.log_file_id,
            "line_number": self.line_number,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "source_ip": self.source_ip,
            "destination_url": self.destination_url,
            "user": self.user,
            "action": self.action,
            "category": self.category,
            "risk_score": self.risk_score,
            "bytes_transferred": self.bytes_transferred,
            "response_time_ms": self.response_time_ms,
            "raw_line": self.raw_line,
            "is_anomalous": self.is_anomalous,
        }
