from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func

from app.extensions import db
from app.models.log_file import LogFile
from app.models.log_entry import LogEntry
from app.models.analysis_result import AnalysisResult
from app.services.analysis_service import analyze_log_file

ANALYSIS_TIMEOUT_MINUTES = 5

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/files", methods=["GET"])
@jwt_required()
def list_files():
    user_id = int(get_jwt_identity())
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    query = LogFile.query.filter_by(user_id=user_id).order_by(LogFile.uploaded_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "files": [f.to_dict() for f in pagination.items],
        "total": pagination.total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "pages": pagination.pages,
    }), 200


@dashboard_bp.route("/files/<int:file_id>", methods=["GET"])
@jwt_required()
def get_file_detail(file_id):
    user_id = int(get_jwt_identity())
    log_file = LogFile.query.filter_by(id=file_id, user_id=user_id).first()
    if not log_file:
        return jsonify({"error": "not_found", "message": "File not found"}), 404
    return jsonify(log_file.to_dict()), 200


@dashboard_bp.route("/files/<int:file_id>/entries", methods=["GET"])
@jwt_required()
def get_entries(file_id):
    user_id = int(get_jwt_identity())
    log_file = LogFile.query.filter_by(id=file_id, user_id=user_id).first()
    if not log_file:
        return jsonify({"error": "not_found", "message": "File not found"}), 404

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    anomalous_only = request.args.get("anomalous_only", "false").lower() == "true"

    query = LogEntry.query.filter_by(log_file_id=file_id)
    if anomalous_only:
        query = query.filter_by(is_anomalous=True)
    query = query.order_by(LogEntry.line_number)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "entries": [e.to_dict() for e in pagination.items],
        "total": pagination.total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "pages": pagination.pages,
    }), 200


@dashboard_bp.route("/files/<int:file_id>/anomalies", methods=["GET"])
@jwt_required()
def get_anomalies(file_id):
    user_id = int(get_jwt_identity())
    log_file = LogFile.query.filter_by(id=file_id, user_id=user_id).first()
    if not log_file:
        return jsonify({"error": "not_found", "message": "File not found"}), 404

    results = (
        AnalysisResult.query
        .filter_by(log_file_id=file_id)
        .order_by(AnalysisResult.confidence_score.desc())
        .all()
    )

    return jsonify({
        "anomalies": [r.to_dict() for r in results],
        "total": len(results),
    }), 200


@dashboard_bp.route("/files/<int:file_id>/analyze", methods=["POST"])
@jwt_required()
def trigger_analysis(file_id):
    user_id = int(get_jwt_identity())
    log_file = LogFile.query.filter_by(id=file_id, user_id=user_id).first()
    if not log_file:
        return jsonify({"error": "not_found", "message": "File not found"}), 404

    if log_file.upload_status != "parsed":
        return jsonify({"error": "bad_request", "message": "File must be parsed before analysis"}), 400

    # Reset stuck "analyzing" status after timeout
    if log_file.analysis_status == "analyzing":
        timeout_threshold = datetime.utcnow() - timedelta(minutes=ANALYSIS_TIMEOUT_MINUTES)
        if log_file.uploaded_at and log_file.uploaded_at < timeout_threshold:
            log_file.analysis_status = "failed"
            db.session.commit()
        else:
            return jsonify({"error": "bad_request", "message": "Analysis already in progress"}), 400

    # Clear previous results if re-analyzing
    if log_file.analysis_status in ("completed", "failed"):
        AnalysisResult.query.filter_by(log_file_id=file_id).delete()
        LogEntry.query.filter_by(log_file_id=file_id).update({"is_anomalous": False})
        db.session.commit()

    try:
        results = analyze_log_file(file_id)
        return jsonify({
            "status": "completed",
            "anomalies_found": len(results),
        }), 200
    except ValueError as e:
        return jsonify({"error": "analysis_error", "message": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "analysis_error", "message": f"Analysis failed: {str(e)}"}), 500


@dashboard_bp.route("/files/<int:file_id>/summary", methods=["GET"])
@jwt_required()
def get_summary(file_id):
    user_id = int(get_jwt_identity())
    log_file = LogFile.query.filter_by(id=file_id, user_id=user_id).first()
    if not log_file:
        return jsonify({"error": "not_found", "message": "File not found"}), 404

    total_entries = LogEntry.query.filter_by(log_file_id=file_id).count()
    total_anomalies = AnalysisResult.query.filter_by(log_file_id=file_id).count()

    severity_breakdown = dict(
        db.session.query(
            AnalysisResult.severity,
            func.count(AnalysisResult.id),
        )
        .filter_by(log_file_id=file_id)
        .group_by(AnalysisResult.severity)
        .all()
    )

    top_anomaly_types = [
        {"type": t, "count": c}
        for t, c in (
            db.session.query(
                AnalysisResult.anomaly_type,
                func.count(AnalysisResult.id),
            )
            .filter_by(log_file_id=file_id)
            .group_by(AnalysisResult.anomaly_type)
            .order_by(func.count(AnalysisResult.id).desc())
            .limit(10)
            .all()
        )
    ]

    return jsonify({
        "total_entries": total_entries,
        "total_anomalies": total_anomalies,
        "severity_breakdown": severity_breakdown,
        "top_anomaly_types": top_anomaly_types,
        "analysis_status": log_file.analysis_status,
        "file": log_file.to_dict(),
    }), 200
