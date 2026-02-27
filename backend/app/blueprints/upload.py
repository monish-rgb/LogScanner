from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models.log_file import LogFile
from app.services.upload_service import save_uploaded_file, parse_uploaded_file, allowed_file

upload_bp = Blueprint("upload", __name__)


@upload_bp.route("/upload", methods=["POST"])
@jwt_required()
def upload_file():
    user_id = int(get_jwt_identity())

    if "file" not in request.files:
        return jsonify({"error": "bad_request", "message": "No file provided"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "bad_request", "message": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "unsupported_file", "message": "Only .log, .txt, and .csv files are supported"}), 415

    log_file, filepath = save_uploaded_file(file, user_id)

    try:
        entry_count = parse_uploaded_file(log_file.id, filepath)
    except ValueError as e:
        return jsonify({"error": "parse_error", "message": str(e)}), 400

    return jsonify({
        "file_id": log_file.id,
        "original_filename": log_file.original_filename,
        "entry_count": entry_count,
        "upload_status": log_file.upload_status,
        "analysis_status": log_file.analysis_status,
    }), 202


@upload_bp.route("/upload/<int:file_id>/status", methods=["GET"])
@jwt_required()
def upload_status(file_id):
    user_id = int(get_jwt_identity())
    log_file = LogFile.query.filter_by(id=file_id, user_id=user_id).first()
    if not log_file:
        return jsonify({"error": "not_found", "message": "File not found"}), 404

    return jsonify({
        "file_id": log_file.id,
        "upload_status": log_file.upload_status,
        "analysis_status": log_file.analysis_status,
        "entry_count": log_file.entry_count,
    }), 200
