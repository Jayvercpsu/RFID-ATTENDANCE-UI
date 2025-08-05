from datetime import datetime, timedelta
from flask import Blueprint, make_response, redirect, request, jsonify, send_from_directory, url_for
import os
import json

import jwt
from utils.auth_utils import SECRET_KEY
from utils.path_utils import get_app_data_dir, get_photo_folder_path, get_student_file_path, load_admin, save_admin
from werkzeug.utils import secure_filename

api_bp = Blueprint('api', __name__)
STUDENT_FILE = os.path.join(get_app_data_dir("CVE_REGISTER"), 'data.json')

@api_bp.route('/api/photo/<filename>')
def get_student_photo(filename):
    photo_dir = get_photo_folder_path()  # This returns APPDATA/CVE_PHOTO
    return send_from_directory(photo_dir, filename)

@api_bp.route('/api/register', methods=['POST'])
def register_student():
    data = request.form.get('data')
    if not data:
        return {"error": "Missing data"}, 400
    student_data = json.loads(data)

    photo_file = request.files.get('photo')
    if photo_file:
        photo_folder = get_photo_folder_path()
        filename = secure_filename(f"{student_data['rfid_code']}.jpg")
        filepath = os.path.join(photo_folder, filename)
        photo_file.save(filepath)
        student_data['photo'] = filename
    else:
        student_data['photo'] = None
# testing comment
    # Save to data.json logic
    students_path = get_app_data_dir("CVE_REGISTER")
    students_file = os.path.join(students_path, "data.json")
    os.makedirs(students_path, exist_ok=True)

    students = []
    if os.path.exists(students_file):
        with open(students_file, "r") as f:
            try:
                students = json.load(f)
            except Exception:
                students = []

    students.append(student_data)

    with open(students_file, "w") as f:
        json.dump(students, f, indent=2)

    occupation = student_data['occupation'] if 'occupation' in student_data else "Student"
    return {"message": f"{occupation} registered successfully!"}

@api_bp.route('/api/logs', methods=['GET'])
def get_logs():
    student_file = get_student_file_path()
    log_type = request.args.get('type', '').lower()

    if not os.path.exists(student_file):
        return jsonify([])

    with open(student_file, 'r') as f:
        students = json.load(f)

     # Filter based on type parameter
    if log_type == 'employee':
        filtered_students = [s for s in students if s.get('occupation', '').lower() == 'employee']
    elif log_type == 'student':
        filtered_students = [s for s in students if s.get('occupation', '').lower() == 'student']
    else:
        filtered_students = students  # No filter if type is not specified or invalid

    # Optional: sort by recent time if `timestamp` exists
    filtered_students.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

    for student in filtered_students:
        photo_filename = student.get("photo")
        if photo_filename:
            student["avatar"] = url_for('api.get_student_photo', filename=photo_filename, _external=True)
        else:
            student["avatar"] = None

    return jsonify(filtered_students)

@api_bp.route('/api/students', methods=['GET'])
def get_students():
    if not os.path.exists(STUDENT_FILE):
        return jsonify([])

    with open(STUDENT_FILE, 'r') as f:
        students = json.load(f)

    # Filter to include both students and records without occupation field
    student_list = [
        student for student in students 
        if 'occupation' not in student or str(student.get('occupation', '')).lower() == 'student'
    ]

    # Attach avatar URLs if photo exists
    for student in student_list:
        photo_filename = student.get("photo")
        if photo_filename:
            student["avatar"] = url_for('api.get_student_photo', filename=photo_filename, _external=True)
        else:
            student["avatar"] = None

    return jsonify(student_list)

@api_bp.route('/api/students/<rfid>', methods=['DELETE'])
def delete_student_by_rfid(rfid):
    if not os.path.exists(STUDENT_FILE):
        return jsonify({'error': 'data.json not found'}), 404

    try:
        with open(STUDENT_FILE, 'r') as f:
            students = json.load(f)

        photo_dir = get_photo_folder_path()
        student_found = False
        updated_students = []

        for student in students:
            if str(student.get('rfid')) == str(rfid) or str(student.get('rfid_code')) == str(rfid):
                student_found = True
                # Attempt to delete photo
                avatar_path = student.get('avatar')
                if avatar_path:
                    try:
                        photo_filename = os.path.basename(avatar_path)
                        photo_full_path = os.path.join(photo_dir, photo_filename)
                        if os.path.exists(photo_full_path):
                            os.remove(photo_full_path)
                    except Exception as e:
                        print(f"Error deleting photo: {e}")
                continue  # Skip adding this student (we're deleting)
            updated_students.append(student)

        if not student_found:
            return jsonify({'error': 'Student not found'}), 404

        with open(STUDENT_FILE, 'w') as f:
            json.dump(updated_students, f, indent=2)

        return jsonify({'message': 'Student and photo deleted successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
 
@api_bp.route('/api/students/<rfid>', methods=['PUT'])
def update_student_by_rfid(rfid):
    if not os.path.exists(STUDENT_FILE):
        return jsonify({'error': 'students.json not found'}), 404

    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400

    updated_data = request.get_json()

    try:
        with open(STUDENT_FILE, 'r') as f:
            students = json.load(f)

        student_found = False
        for student in students:
            student_rfid = student.get('rfid') or student.get('rfid_code')
            if student_rfid == rfid:
                student.update(updated_data)
                student_found = True
                break

        if not student_found:
            return jsonify({'error': 'Student not found'}), 404

        with open(STUDENT_FILE, 'w') as f:
            json.dump(students, f, indent=2)

        return jsonify({'message': 'Student updated successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/api/log', methods=['POST'])
def log_attendance():
    log_file_path = get_student_file_path()
    student_file_path = os.path.join(get_app_data_dir(), "data.json")

    try:
        data = request.json
        rfid_code = data.get("rfid")

        if not rfid_code:
            return jsonify({"error": "RFID is required"}), 400

        # Load student list
        if not os.path.exists(student_file_path):
            return jsonify({"error": "data.json not found"}), 404

        with open(student_file_path, "r") as sf:
            students = json.load(sf)

        # Match student
        matched_student = next((
            s for s in students
            if s.get("rfid") == rfid_code or s.get("rfid_code") == rfid_code
        ), None)

        if not matched_student:
            return jsonify({"error": "Student not found"}), 404

        # Load logs
        logs = []
        if os.path.exists(log_file_path) and os.path.getsize(log_file_path) > 0:
            with open(log_file_path, 'r') as lf:
                logs = json.load(lf)

        # Determine today's date string
        today = datetime.now().date().isoformat()

        # Check today's logs for this student
        todays_logs = [
            log for log in logs
            if log.get("rfid") == rfid_code and log.get("timestamp", "").startswith(today)
        ]

        # Group today's logs by status
        today_in = any(log.get("status") == "IN" for log in todays_logs)
        today_out = any(log.get("status") == "OUT" for log in todays_logs)

        # Prevent more than one IN and OUT per day
        if today_in and today_out:
            return jsonify({"error": "Already timed in and out for today."}), 403

        # Assign status based on today's logs
        if not today_in:
            status = "IN"
        elif not today_out:
            status = "OUT"
        else:
            return jsonify({"error": "Unable to determine status."}), 500

        # Handle photo and avatar
        photo_filename = matched_student.get("photo")
        avatar_url = url_for('api.get_student_photo', filename=photo_filename, _external=True) if photo_filename else None

        # Build new log entry
        log_entry = {
        "student_id": rfid_code,
        "rfid": rfid_code,
        "timestamp": datetime.now().isoformat(),
        "status": status,
        "first_name": matched_student.get("first_name", ""),
        "middle_name": matched_student.get("middle_name", ""),
        "last_name": matched_student.get("last_name", ""),
        "age": matched_student.get("age", ""),  # ✅ ADD THIS LINE
        "grade": matched_student.get("grade", ""),
        "strandOrSec": matched_student.get("section", ""),
        "gender": matched_student.get("gender", ""),
        "guardian": matched_student.get("guardian", ""),
        "occupation": matched_student.get("occupation", ""),
        "id_number": matched_student.get("id_number", ""),
        "contact": matched_student.get("contact", ""),
        "address": matched_student.get("address", ""),
        "photo": photo_filename,
        "avatar": avatar_url
        }

        # Append log and save
        logs.append(log_entry)

        with open(log_file_path, 'w') as lf:
            json.dump(logs, lf, indent=2)

        return jsonify({
            "message": f"Log entry saved successfully as {status}",
            "status": status
        }), 200
        

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/api/dashboard-stats', methods=['GET'])
def get_dashboard_stats():
    try:
        student_file = os.path.join(get_app_data_dir(), "data.json")
        employee_file = os.path.join(get_app_data_dir(), "employees.json")
        log_file = get_student_file_path()

        # Load student records
        with open(student_file, 'r') as sf:
            students = json.load(sf)

        # Load employees
        employees = []
        if os.path.exists(employee_file):
            with open(employee_file, 'r') as ef:
                employees = json.load(ef)

        # Load attendance logs
        logs = []
        if os.path.exists(log_file) and os.path.getsize(log_file) > 0:
            with open(log_file, 'r') as lf:
                logs = json.load(lf)

        today_str = datetime.now().date().isoformat()
        today_logs = [log for log in logs if log["timestamp"].startswith(today_str)]

        # Breakdown
        total_students = len([s for s in students if s.get("occupation", "").lower() == "student"])
        total_employees = len([e for e in students if e.get("occupation", "").lower() == "employee"]) + len(employees)

        time_in_today = len([log for log in today_logs if log["status"] == "IN"])
        time_out_today = len([log for log in today_logs if log["status"] == "OUT"])

        # Count unique students present today
        present_rfids = set(log["rfid"] for log in today_logs if log["status"] == "IN")
        present_today = len(present_rfids)

        recent_logs = sorted(today_logs, key=lambda l: l["timestamp"], reverse=True)[:3]

        return jsonify({
            "total_students": total_students,
            "present_today": present_today,
            "time_in_today": time_in_today,
            "time_out_today": time_out_today,
            "total_employees": total_employees,
            "recent_logs": recent_logs
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/api/admin-login', methods=['POST'])
def admin_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    admin = load_admin()

    if username == admin['username'] and password == admin['password']:
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
    
@api_bp.route('/api/admin-reset', methods=['POST'])
def reset_admin_credentials():
    try:
        admin_data = load_admin()
        default_user = admin_data['default_username']
        default_password = admin_data['default_password']

        # Validate required fields
        if not default_user or not default_password:
            return jsonify({
                "success": False,
                "message": "Missing default username or password in admin.json"
            }), 400

        # Apply reset
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

@api_bp.route('/api/update-employee', methods=['POST'])
def update_attendance():
    try:
        data = request.json
        rfid = data.get('rfid')
        date = data.get('date')
        time_in = data.get('time_in')
        time_out = data.get('time_out')
        original_time_in = data.get('original_time_in')
        original_time_out = data.get('original_time_out')

        if not all([rfid, date, time_in]):
            return jsonify({'error': 'Missing required fields'}), 400

        # Load the logs file
        log_file_path = get_student_file_path()
        if not os.path.exists(log_file_path):
            return jsonify({'error': 'Logs file not found'}), 404

        with open(log_file_path, 'r') as f:
            logs = json.load(f)

        # Convert input date/time to datetime objects
        new_time_in_dt = datetime.strptime(f"{date}T{time_in}", "%Y-%m-%dT%H:%M")
        if time_out:
            new_time_out_dt = datetime.strptime(f"{date}T{time_out}", "%Y-%m-%dT%H:%M")
            if new_time_out_dt <= new_time_in_dt:
                return jsonify({'error': 'Time out must be after time in'}), 400

        updated = False

        # Update the logs
        for log in logs:
            if log.get('rfid') == rfid:
                log_dt = datetime.fromisoformat(log['timestamp'])
                log_date = log_dt.date().isoformat()
                
                # Check if this log matches the original time in/out we're updating
                if (original_time_in and log['timestamp'] == original_time_in) or \
                   (original_time_out and log['timestamp'] == original_time_out):
                    
                    # Update the timestamp
                    if log['status'] == 'IN':
                        log['timestamp'] = new_time_in_dt.isoformat()
                        updated = True
                    elif log['status'] == 'OUT' and time_out:
                        log['timestamp'] = new_time_out_dt.isoformat()
                        updated = True

        if updated:
            # Save the updated logs
            with open(log_file_path, 'w') as f:
                json.dump(logs, f, indent=2)
            
            return jsonify({'message': 'Attendance updated successfully'}), 200
        else:
            return jsonify({'error': 'No matching records found to update'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@api_bp.route('/api/admin-logout')
def admin_logout():
    resp = make_response(redirect(url_for('pages.admin_login')))
    resp.delete_cookie('admin_token')
    return resp