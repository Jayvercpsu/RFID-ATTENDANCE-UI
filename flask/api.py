from flask import Blueprint, request
from Service.adminService import admin_login_service, admin_logout_service, reset_admin_credentials_service
from Service.logService import get_dashboard_stats_service, get_logs_service, log_attendance_service, update_attendance_service
from Service.userService import check_rfid_service, delete_student_service, get_student_photo_file_response, get_students_service, register_student_logic, update_student_service
from config import HTTPMethod

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/photo/<filename>')
def get_student_photo(filename):
    return get_student_photo_file_response(filename)

@api_bp.route('/api/register', methods=[HTTPMethod.POST])
def register_student():
    return register_student_logic(request.form, request.files)

@api_bp.route('/api/logs', methods=[HTTPMethod.GET])
def get_logs():
    return get_logs_service(request.args)

@api_bp.route('/api/students', methods=[HTTPMethod.GET])
def get_students():
    return get_students_service(request)

@api_bp.route('/api/students/<rfid>', methods=[HTTPMethod.DELETE])
def delete_student_by_rfid(rfid):
    return delete_student_service(rfid)
 
@api_bp.route('/api/students/<rfid>', methods=[HTTPMethod.PUT])
def update_student_by_rfid(rfid):
    return update_student_service(rfid, request)

@api_bp.route('/api/log', methods=[HTTPMethod.POST])
def log_attendance():
    return log_attendance_service(request)

@api_bp.route('/api/dashboard-stats', methods=[HTTPMethod.GET])
def get_dashboard_stats():
    return get_dashboard_stats_service()

@api_bp.route('/api/admin-login', methods=[HTTPMethod.POST])
def admin_login():
    return admin_login_service(request)
    
@api_bp.route('/api/admin-reset', methods=[HTTPMethod.POST])
def reset_admin_credentials():
    return reset_admin_credentials_service()

@api_bp.route('/api/update-employee', methods=[HTTPMethod.POST])
def update_attendance():
    return update_attendance_service(request)

@api_bp.route('/api/check-rfid', methods=[HTTPMethod.POST])
def check_rfid():
    return check_rfid_service(request)

@api_bp.route('/api/admin-logout', methods=[HTTPMethod.GET])
def admin_logout():
    return admin_logout_service()