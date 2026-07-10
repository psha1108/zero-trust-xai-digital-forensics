from flask import Blueprint, render_template
from flask_login import login_required, current_user

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def home():
    """
    Placeholder dashboard. Right now it just proves login/session works.
    From Step 8 onward this will display: latest risk score, SHAP
    explanation, recent alerts. From Step 12 onward: full Chart.js views.
    """
    return render_template("dashboard.html", user=current_user)
