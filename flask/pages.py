# Create a Blueprint for pages
from flask import Blueprint, render_template

from config import ADMIN_DASHBOARD_PAGE, ADMIN_LOGIN_PAGE, ADMIN_STUDENTS_PAGE, MAIN_PAGE


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

@pages_bp.route("/admin/students")
def admin_students():
    return render_template(ADMIN_STUDENTS_PAGE)

@pages_bp.route("/admin/attendance-logs")
def admin_attendance_logs():
    return render_template(ADMIN_ATTENDANCE_LOGS_PAGE)