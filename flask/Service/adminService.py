from datetime import datetime, timedelta
import os
import tempfile
import zipfile
import bcrypt
from flask import jsonify, make_response, redirect, url_for
import jwt

from Repository.adminRepository import cleanup_temp_dir, create_backup_zip, extract_backup_zip, restore_backup_files, save_uploaded_backup
from utils.auth_utils import SECRET_KEY
from utils.path_utils import load_admin, save_admin


def admin_login_service(request):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "Missing JSON body"}), 400

        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({"success": False, "message": "Username and password required"}), 400

        admin = load_admin()

        if username == admin["username"] and bcrypt.checkpw(password.encode(), admin["password"].encode()):
            exp = datetime.utcnow() + timedelta(hours=24)
            token = jwt.encode({"username": username, "exp": exp}, SECRET_KEY, algorithm="HS256")

            resp = make_response(jsonify({"success": True}))
            resp.set_cookie(
                'admin_token',
                token,
                httponly=True,
                expires=exp,
                samesite='Lax'
            )
            return resp, 200
        else:
            return jsonify({"success": False, "message": "Incorrect credentials"}), 401

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


def reset_admin_credentials_service():
    try:
        admin_data = load_admin()
        default_user = admin_data.get('default_username')
        default_password = admin_data.get('default_password')

        if not default_user or not default_password:
            return jsonify({
                "success": False,
                "message": "Missing default username or password in admin.json"
            }), 400

        admin_data['username'] = default_user
        admin_data['password'] = default_password

        save_admin(admin_data)

        return jsonify({
            "success": True,
            "message": "Admin credentials reset to default."
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Failed to reset credentials: {str(e)}"
        }), 500
    

def get_settings_service():
    try:
        admin_data = load_admin()
        return jsonify({
            "username": admin_data.get("username", "admin"),
            "backup_path": admin_data.get("backup_path", "")
        }), 200
    except Exception as e:
        return jsonify({
            "error": str(e),
            "message": "Failed to load settings"
        }), 500
    

def admin_logout_service():
    resp = make_response(redirect(url_for('pages.admin_login')))
    resp.delete_cookie('admin_token')
    return resp


def update_profile_service(request):
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Missing JSON body"}), 400

        admin_data = load_admin()

        current_pw = data.get("currentPassword")
        if not current_pw or not bcrypt.checkpw(current_pw.encode(), admin_data["password"].encode()):
            return jsonify({"error": "Current password is incorrect"}), 401

        # Update username if provided
        new_username = data.get("username")
        if new_username:
            admin_data["username"] = new_username

        # Update password if provided (hash it)
        new_password = data.get("newPassword")
        if new_password:
            hashed_pw = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
            admin_data["password"] = hashed_pw

        save_admin(admin_data)
        return jsonify({"message": "Profile updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def create_backup_service(request):
    try:
        data = request.json
        if not data or 'backup_path' not in data or not data['backup_path']:
            return jsonify({"error": "No backup path provided"}), 400

        backup_path = data['backup_path']

        backup_full = create_backup_zip(backup_path)

        # Save backup path in admin settings
        admin_data = load_admin()
        admin_data['backup_path'] = backup_path
        save_admin(admin_data)

        return jsonify({"success": True, "backup_path": backup_full}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

def restore_backup_service(request):
    if 'backupFile' not in request.files:
        return jsonify({"error": "No backup file provided"}), 400

    file = request.files['backupFile']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_zip_path = os.path.join(temp_dir, file.filename)
            file.save(temp_zip_path)

            extract_path = os.path.join(temp_dir, 'extracted')
            os.makedirs(extract_path, exist_ok=True)
            with zipfile.ZipFile(temp_zip_path, 'r') as z:
                z.extractall(extract_path)

            restore_backup_files(extract_path)

        return jsonify({"success": True}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500