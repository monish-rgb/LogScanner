from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
)

from app.services.auth_service import register_user, authenticate_user
from app.models.user import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"error": "bad_request", "message": "JSON body required"}), 400

    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not username or not email or not password:
        return jsonify({"error": "validation_error", "message": "Username, email, and password are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "validation_error", "message": "Password must be at least 6 characters"}), 400

    try:
        user = register_user(username, email, password)
    except ValueError as e:
        return jsonify({"error": "validation_error", "message": str(e)}), 409

    return jsonify(user.to_dict()), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "bad_request", "message": "JSON body required"}), 400

    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "validation_error", "message": "Username and password are required"}), 400

    user = authenticate_user(username, password)
    if not user:
        return jsonify({"error": "unauthorized", "message": "Invalid username or password"}), 401

    access_token = create_access_token(identity=str(user.id))

    return jsonify({
        "access_token": access_token,
        "user": user.to_dict(),
    }), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user:
        return jsonify({"error": "not_found", "message": "User not found"}), 404
    return jsonify(user.to_dict()), 200
