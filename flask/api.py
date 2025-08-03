from datetime import datetime
from flask import Blueprint, request, jsonify, send_from_directory, url_for
import os
import json
from utils.path_utils import get_app_data_dir, get_photo_folder_path, get_student_file_path
from werkzeug.utils import secure_filename

api_bp = Blueprint('api', __name__)
STUDENT_FILE = os.path.join(get_app_data_dir(), 'students.json')

# @api_bp.route('/api/register', methods=['POST'])
# def register_student():
#     try:
#         data = request.json

#         # Load current data
#         if os.path.exists(STUDENT_FILE):
#             with open(STUDENT_FILE, 'r') as f:
#                 content = f.read().strip()
#                 students = json.loads(content) if content else []
#         else:
#             students = []

#         students.append(data)

#         # Save updated data
#         with open(STUDENT_FILE, 'w') as f:
#             json.dump(students, f, indent=2)

#         return jsonify({"message": "Student registered successfully!"}), 200
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

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
    # Save to students.json logic
    students_path = get_app_data_dir("CVE_REGISTER")
    students_file = os.path.join(students_path, "students.json")
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

    return {"message": "Student registered successfully!"}
    
@api_bp.route('/api/logs', methods=['GET'])
def get_logs():
    student_file = get_student_file_path()

    if not os.path.exists(student_file):
        return jsonify([])

    with open(student_file, 'r') as f:
        students = json.load(f)

    # Optional: sort by recent time if `timestamp` exists
    students.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

    for student in students:
        photo_filename = student.get("photo")
        if photo_filename:
            student["avatar"] = url_for('api.get_student_photo', filename=photo_filename, _external=True)
        else:
            student["avatar"] = None

    return jsonify(students)

@api_bp.route('/api/log', methods=['POST'])
def log_attendance():
    log_file_path = get_student_file_path()
    student_file_path = os.path.join(get_app_data_dir(), "students.json")

    try:
        data = request.json
        rfid_code = data.get("rfid")

        if not rfid_code:
            return jsonify({"error": "RFID is required"}), 400

        # Load student list
        if not os.path.exists(student_file_path):
            return jsonify({"error": "students.json not found"}), 404

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

        # Determine new status: alternate IN/OUT
        status = "IN" if len(todays_logs) % 2 == 0 else "OUT"

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