from flask import Blueprint, request, jsonify
import os
import json
from utils.path_utils import get_app_data_dir, get_student_file_path

api_bp = Blueprint('api', __name__)
STUDENT_FILE = os.path.join(get_app_data_dir(), 'students.json')

@api_bp.route('/api/register', methods=['POST'])
def register_student():
    try:
        data = request.json

        # Load current data
        if os.path.exists(STUDENT_FILE):
            with open(STUDENT_FILE, 'r') as f:
                students = json.load(f)
        else:
            students = []

        students.append(data)

        # Save updated data
        with open(STUDENT_FILE, 'w') as f:
            json.dump(students, f, indent=2)

        return jsonify({"message": "Student registered successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@api_bp.route('/api/logs', methods=['GET'])
def get_logs():
    student_file = get_student_file_path()

    if not os.path.exists(student_file):
        return jsonify([])

    with open(student_file, 'r') as f:
        students = json.load(f)

    # Optional: sort by recent time if `timestamp` exists
    students.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

    return jsonify(students)