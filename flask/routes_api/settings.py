import shutil
import zipfile
from flask import Blueprint, request, jsonify
import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from utils.path_utils import get_app_data_dir, get_student_file_path, get_photo_folder_path, load_admin, save_admin

settings_bp = Blueprint('settings', __name__)

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

@settings_bp.route('/api/create-backup', methods=['POST'])
def create_backup():
    data = request.json
    backup_path = data.get("backup_path")

    if not backup_path:
        return jsonify({"error":"No backup path provided"}), 400

    # Auto-create the destination folder if it does not exist
    try:
        os.makedirs(backup_path, exist_ok=True)
    except Exception as e:
        return jsonify({"error": f"Cannot create backup folder: {e}"}), 500
    
    folders = ["CVE_ATTENDANCE", "CVE_PHOTO", "CVE_REGISTER"]
    appdata = os.getenv('APPDATA', os.path.expanduser("~"))

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"rfid_backup_{timestamp}.zip"
    backup_full = os.path.join(backup_path, backup_filename)

    try:
        with zipfile.ZipFile(backup_full, 'w', zipfile.ZIP_DEFLATED) as z:
            for folder in folders:
                folder_path = os.path.join(appdata, folder)
                if os.path.exists(folder_path):
                    for root,dirs,files in os.walk(folder_path):
                        for f in files:
                            file_path = os.path.join(root, f)
                            arcname = os.path.join(folder, os.path.relpath(file_path,folder_path))
                            z.write(file_path, arcname)
        return jsonify({"success": True,"backup_path":backup_full })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@settings_bp.route('/api/restore-backup', methods=['POST'])
def restore_backup():
    if 'backupFile' not in request.files:
        return jsonify({"error": "No backup file provided"}), 400
    file = request.files['backupFile']
    if file.filename == '':
        return jsonify({"error": "No selected file"}),400

    try:
        temp_dir = os.path.join(os.getenv('APPDATA', os.path.expanduser('~')), 'rfid_temp')
        os.makedirs(temp_dir, exist_ok=True)

        filename = file.filename
        temp_zip_path = os.path.join(temp_dir, filename)
        file.save(temp_zip_path)

        extract_path = os.path.join(temp_dir,'extracted')
        with zipfile.ZipFile(temp_zip_path,'r') as z:
            z.extractall(extract_path)

        appdata = os.getenv('APPDATA', os.path.expanduser('~'))
        for folder in os.listdir(extract_path):
            src = os.path.join(extract_path, folder)
            dst = os.path.join(appdata, folder)
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.move(src,dst)

        shutil.rmtree(temp_dir, ignore_errors=True)
        return jsonify({"success":True})
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return jsonify({"error":str(e)}),500

@settings_bp.route('/api/set-backup-path', methods=['POST'])
def set_backup_path():
    data = request.json
    path = data.get('path')
    
    if not path:
        return jsonify({"error": "No path provided"}), 400
    
    # In a real app, you would save this to your settings
    return jsonify({
        "message": "Backup path updated",
        "path": path
    })

@settings_bp.route('/api/get-backup-path', methods=['GET'])
def get_backup_path():
    # In a real app, you would get this from your settings
    return jsonify({
        "backup_path": os.path.join(os.getenv('APPDATA', os.path.expanduser('~')), 'backups')
    })

