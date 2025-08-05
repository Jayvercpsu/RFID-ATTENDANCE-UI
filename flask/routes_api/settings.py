import zipfile
from flask import Blueprint, request, jsonify
import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from utils.path_utils import get_app_data_dir, get_student_file_path, get_photo_folder_path, load_admin, save_admin

settings_bp = Blueprint('settings', __name__)

# Initialize default settings in admin.json if they don't exist
def init_settings():
    admin_data = load_admin()
    defaults = {
        "backup_path": os.path.join(get_app_data_dir(), "backups"),
        "default_username": "admin",
        "default_password": "admin123"
    }
    
    # Set defaults if they don't exist
    updated = False
    for key, value in defaults.items():
        if key not in admin_data:
            admin_data[key] = value
            updated = True
    
    if updated:
        save_admin(admin_data)

# Initialize settings when module loads
init_settings()

@settings_bp.route('/api/get-settings', methods=['GET'])
def get_settings():
    admin_data = load_admin()
    # Return only non-sensitive settings
    return jsonify({
        "username": admin_data.get("username"),
        "backup_path": admin_data.get("backup_path")
    })

@settings_bp.route('/api/update-profile', methods=['POST'])
def update_profile():
    data = request.json
    admin_data = load_admin()
    
    # Validate current password
    if 'currentPassword' not in data or data['currentPassword'] != admin_data.get("password"):
        return jsonify({"error": "Current password is incorrect"}), 401
    
    # Update username if provided
    if 'username' in data:
        admin_data['username'] = data['username']
    
    # Update password if new password provided
    if 'newPassword' in data and data['newPassword']:
        admin_data['password'] = data['newPassword']
    
    save_admin(admin_data)
    return jsonify({"message": "Profile updated successfully"})

@settings_bp.route('/api/set-backup-location', methods=['POST'])
def set_backup_location():
    data = request.json
    path = data.get('path')
    
    if not path:
        return jsonify({"error": "No path provided"}), 400
    
    # Validate path exists and is writable
    if not os.path.exists(path):
        return jsonify({"error": "Path does not exist"}), 400
    if not os.access(path, os.W_OK):
        return jsonify({"error": "Path is not writable"}), 400
    
    admin_data = load_admin()
    admin_data['backup_path'] = path
    save_admin(admin_data)
    
    return jsonify({
        "message": "Backup location updated",
        "path": path
    })

@settings_bp.route('/api/create-backup', methods=['POST'])
def create_backup():
    data = request.json
    admin_data = load_admin()
    backup_path = data.get('location') or admin_data.get('backup_path')
    
    if not backup_path:
        return jsonify({"error": "No backup location configured"}), 400
    
    try:
        # Ensure backup directory exists
        os.makedirs(backup_path, exist_ok=True)
        
        # Create backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"attendance_backup_{timestamp}.zip"
        backup_fullpath = os.path.join(backup_path, backup_filename)
        
        # Get paths to important files to backup
        files_to_backup = [
            get_student_file_path(),  # logs.json
            os.path.join(get_app_data_dir("CVE_REGISTER"), "data.json"),  # student data
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'credentials', 'admin.json')  # settings
        ]
        
        # Create zip archive
        with zipfile.ZipFile(backup_fullpath, 'w') as zipf:
            for file in files_to_backup:
                if os.path.exists(file):
                    arcname = os.path.basename(file)
                    zipf.write(file, arcname)
        
        return jsonify({
            "message": "Backup created successfully",
            "path": backup_fullpath,
            "filename": backup_filename
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@settings_bp.route('/api/restore-backup', methods=['POST'])
def restore_backup():
    if 'backupFile' not in request.files:
        return jsonify({"error": "No backup file provided"}), 400
    
    backup_file = request.files['backupFile']
    if backup_file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    try:
        # Create temp directory in app data folder
        temp_dir = os.path.join(get_app_data_dir(), "temp")
        os.makedirs(temp_dir, exist_ok=True)
        
        # Save uploaded file temporarily
        filename = secure_filename(backup_file.filename)
        temp_path = os.path.join(temp_dir, filename)
        backup_file.save(temp_path)
        
        # Define restore locations
        restore_locations = {
            "logs.json": get_student_file_path(),
            "data.json": os.path.join(get_app_data_dir("CVE_REGISTER"), "data.json"),
            "admin.json": os.path.join(os.path.dirname(os.path.dirname(__file__)), 'credentials', 'admin.json')
        }
        
        # Extract and restore files
        with zipfile.ZipFile(temp_path, 'r') as zipf:
            for file in zipf.namelist():
                if file in restore_locations:
                    # Extract to temp location first
                    temp_extract = os.path.join(temp_dir, file)
                    with open(temp_extract, 'wb') as f:
                        f.write(zipf.read(file))
                    
                    # Then move to final location
                    os.replace(temp_extract, restore_locations[file])
        
        # Clean up
        os.remove(temp_path)
        
        return jsonify({"message": "Backup restored successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # Clean up any remaining temp files
        if 'temp_extract' in locals():
            if os.path.exists(temp_extract):
                os.remove(temp_extract)