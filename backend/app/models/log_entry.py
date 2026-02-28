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
    department = db.Column(db.String(100), nullable=True)
    location = db.Column(db.String(100), nullable=True)
    protocol = db.Column(db.String(20), nullable=True)
    request_method = db.Column(db.String(10), nullable=True)
    server_ip = db.Column(db.String(45), nullable=True)
    response_size = db.Column(db.BigInteger, nullable=True)
    request_size = db.Column(db.BigInteger, nullable=True)
    status_code = db.Column(db.Integer, nullable=True)
    content_type = db.Column(db.String(100), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    threat_name = db.Column(db.String(200), nullable=True)
    threat_class = db.Column(db.String(100), nullable=True)
    threat_category = db.Column(db.String(100), nullable=True)
    threat_severity = db.Column(db.String(50), nullable=True)
    file_type = db.Column(db.String(100), nullable=True)
    file_class = db.Column(db.String(100), nullable=True)
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
            "department": self.department,
            "location": self.location,
            "protocol": self.protocol,
            "request_method": self.request_method,
            "server_ip": self.server_ip,
            "response_size": self.response_size,
            "request_size": self.request_size,
            "status_code": self.status_code,
            "content_type": self.content_type,
            "user_agent": self.user_agent,
            "threat_name": self.threat_name,
            "threat_class": self.threat_class,
            "threat_category": self.threat_category,
            "threat_severity": self.threat_severity,
            "file_type": self.file_type,
            "file_class": self.file_class,
            "raw_line": self.raw_line,
            "is_anomalous": self.is_anomalous,
        }
