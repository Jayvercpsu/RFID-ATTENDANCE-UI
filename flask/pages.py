# Create a Blueprint for pages
from flask import Blueprint, render_template

from config import ADMIN_DASHBOARD_PAGE, ADMIN_LOGIN_PAGE, MAIN_PAGE


pages_bp = Blueprint("pages", __name__)

@pages_bp.route("/")
def home():
    return render_template(MAIN_PAGE)

@pages_bp.route("/admin/login")
def admin_login():
    return render_template(ADMIN_LOGIN_PAGE)

@pages_bp.route("/admin/dashboard")
def admin_dashboard():
    return render_template(ADMIN_DASHBOARD_PAGE)