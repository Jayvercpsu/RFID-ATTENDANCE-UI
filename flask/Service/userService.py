import json
import os
from flask import jsonify, send_from_directory, abort, url_for
from Repository.userRepository import check_rfid_exists, delete_photo_file, delete_student_by_id, fetch_photo_file, fetch_students, find_student_by_rfid, find_user_by_rfid, get_user_table_columns, insert_student, save_student_photo, update_student_by_rfid
from db import get_db_connection

def get_student_photo_file_response(filename: str):
    photo_dir = fetch_photo_file(filename)
    file_path = os.path.join(photo_dir, filename)
    if not os.path.isfile(file_path):
        abort(404, description="Photo not found")
    return send_from_directory(photo_dir, filename)


def register_student_logic(form_data, files):
    try:
        data = form_data.get('data')
        if not data:
            return jsonify({"error": "Missing data"}), 400

        student_data = json.loads(data)

        photo_file = files.get('photo')
        if photo_file:
            filename = save_student_photo(photo_file, student_data['rfid_code'])
            student_data['photo'] = filename
        else:
            student_data['photo'] = None

        if check_rfid_exists(student_data.get('rfid_code')):
            return jsonify({"error": "RFID already exists in database"}), 400

        insert_student(student_data)

        occupation = student_data.get('occupation', "Student")
        return jsonify({"message": f"{occupation} registered successfully!"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

   
def delete_student_service(rfid):
    try:
        student = find_student_by_rfid(rfid)
        if not student:
            return jsonify({'error': 'Student not found'}), 404

        student_id, photo_filename = student
        delete_photo_file(photo_filename)
        delete_student_by_id(student_id)

        return jsonify({'message': 'Student and photo deleted successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def update_student_service(rfid, request_obj):
    try:
        if not request_obj.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400

        updated_data = request_obj.get_json()

        columns = get_user_table_columns()
        updatable_fields = [col for col in columns if col != 'rfid_code']

        filtered_data = {k: v for k, v in updated_data.items() if k in updatable_fields}

        if not filtered_data:
            return jsonify({'error': 'No valid fields to update'}), 400

        updated_rows = update_student_by_rfid(rfid, filtered_data)
        if updated_rows == 0:
            return jsonify({'error': 'Student not found'}), 404

        return jsonify({'message': 'Student updated successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

 
def check_rfid_service(request):
    try:
        data = request.get_json()
        if not data or 'rfid_code' not in data:
            return jsonify({"error": "RFID code is required"}), 400

        rfid_code = data['rfid_code']
        conn = get_db_connection()
        
        user = find_user_by_rfid(conn, rfid_code)
        conn.close()
        if user:
            return jsonify({
                "exists": True,
                "student": dict(user),
                "message": "RFID found in database"
            }), 200
        else:
            return jsonify({
                "exists": False,
                "message": "RFID not found in database"
            }), 200
        

    except Exception as e:
        return jsonify({
            "error": str(e),
            "message": "Error checking RFID"
        }), 500


def get_students_service():
    try:
        rows = fetch_students()
        student_list = []

        for row in rows:
            student = dict(row)
            photo = student.get("photo")
            student["avatar"] = url_for(
                'api.get_student_photo',
                filename=photo,
                _external=True
            ) if photo else None
            student_list.append(student)

        return jsonify(student_list), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
