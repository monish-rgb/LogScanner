import os
import uuid

from flask import current_app
from app.extensions import db
from app.models.log_file import LogFile
from app.models.log_entry import LogEntry
from app.parsers import get_parser


ALLOWED_EXTENSIONS = {"log", "txt", "csv"}
BATCH_SIZE = 1000


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_file(file, user_id):
    original_filename = file.filename
    ext = original_filename.rsplit(".", 1)[1].lower() if "." in original_filename else "log"
    stored_filename = f"{uuid.uuid4().hex}.{ext}"

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    filepath = os.path.join(upload_folder, stored_filename)
    file.save(filepath)

    file_size = os.path.getsize(filepath)

    log_file = LogFile(
        user_id=user_id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_size=file_size,
        file_type=ext,
        upload_status="processing",
        analysis_status="pending",
    )
    db.session.add(log_file)
    db.session.commit()

    return log_file, filepath


def parse_uploaded_file(log_file_id, filepath):
    log_file = LogFile.query.get(log_file_id)
    if not log_file:
        raise ValueError("Log file not found")

    try:
        parser = get_parser(filepath)
    except ValueError as e:
        log_file.upload_status = "failed"
        db.session.commit()
        raise e

    batch = []
    count = 0

    for parsed in parser.parse_file(filepath, log_file_id):
        entry = LogEntry(
            log_file_id=parsed.get("log_file_id", log_file_id),
            line_number=parsed.get("line_number", count + 1),
            timestamp=parsed.get("timestamp"),
            source_ip=parsed.get("source_ip"),
            destination_url=parsed.get("destination_url"),
            user=parsed.get("user"),
            action=parsed.get("action"),
            category=parsed.get("category"),
            risk_score=parsed.get("risk_score"),
            bytes_transferred=parsed.get("bytes_transferred"),
            response_time_ms=parsed.get("response_time_ms"),
            raw_line=parsed.get("raw_line", ""),
            is_anomalous=False,
        )
        batch.append(entry)
        count += 1

        if len(batch) >= BATCH_SIZE:
            db.session.bulk_save_objects(batch)
            db.session.commit()
            batch = []

    if batch:
        db.session.bulk_save_objects(batch)
        db.session.commit()

    log_file.entry_count = count
    log_file.upload_status = "parsed"
    db.session.commit()

    return count
