from flask import Blueprint, jsonify
from flask_login import login_required, current_user

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api")


@dashboard_bp.route("/dashboard", methods=["GET"])
@login_required
def home():
    return jsonify({
        "username": current_user.username,
        "role": current_user.role,
        "message": "Dashboard placeholder — risk score, SHAP, and alerts arrive in later steps.",
    }), 200