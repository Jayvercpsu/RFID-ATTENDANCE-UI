from enum import Enum


MAIN_PAGE = "pages/index.html"
ADMIN_LOGIN_PAGE = "pages/admin/admin-login.html"
ADMIN_FORGOT_PASSWORD_PAGE = "pages/admin/admin-forgot-password.html"
ADMIN_DASHBOARD_PAGE = "pages/admin/dashboard.html"
ADMIN_STUDENTS_PAGE = "pages/admin/students.html"
ADMIN_ATTENDANCE_LOGS_PAGE = "pages/admin/attendance-logs.html"
ADMIN_EMPLOYEE_LOGS_PAGE = "pages/admin/employee-logs.html"
ADMIN_SETTINGS_PAGE = "pages/admin/settings.html"

class HTTPMethod(str, Enum):
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'
    PATCH = 'PATCH'