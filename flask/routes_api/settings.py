from flask import Blueprint, request
from Service.adminService import create_backup_service, get_settings_service, restore_backup_service, update_profile_service
from config import HTTPMethod

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/api/get-settings', methods=[HTTPMethod.GET])
def get_settings():
    return get_settings_service()


@settings_bp.route('/api/update-profile', methods=[HTTPMethod.POST])
def update_profile():
    return update_profile_service(request)


@settings_bp.route('/api/create-backup', methods=[HTTPMethod.POST])
def create_backup():
    return create_backup_service(request)


@settings_bp.route('/api/restore-backup', methods=[HTTPMethod.POST])
def restore_backup():
    return restore_backup_service(request)
