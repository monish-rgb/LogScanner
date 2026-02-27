from flask import jsonify
from werkzeug.exceptions import HTTPException


def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "bad_request", "message": str(e.description)}), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({"error": "unauthorized", "message": "Authentication required"}), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({"error": "forbidden", "message": "Access denied"}), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "not_found", "message": "Resource not found"}), 404

    @app.errorhandler(413)
    def too_large(e):
        return jsonify({"error": "file_too_large", "message": "File exceeds maximum size"}), 413

    @app.errorhandler(415)
    def unsupported_media(e):
        return jsonify({"error": "unsupported_file", "message": "Unsupported file type"}), 415

    @app.errorhandler(422)
    def unprocessable(e):
        return jsonify({"error": "validation_error", "message": str(e.description)}), 422

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "internal_error", "message": "An internal error occurred"}), 500

    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        return jsonify({"error": e.name.lower().replace(" ", "_"), "message": e.description}), e.code
