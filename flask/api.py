from datetime import datetime, timedelta
import sqlite3
import bcrypt
from flask import Blueprint, make_response, redirect, request, jsonify, send_from_directory, url_for
import os
import json

import jwt
from db import get_db_connection
from utils.auth_utils import SECRET_KEY
from utils.path_utils import get_photo_folder_path, load_admin, save_admin
from werkzeug.utils import secure_filename

api_bp = Blueprint('api', __name__)

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

    # Handle photo upload
    photo_file = request.files.get('photo')
    if photo_file:
        photo_folder = get_photo_folder_path()
        os.makedirs(photo_folder, exist_ok=True)
        filename = secure_filename(f"{student_data['rfid_code']}.jpg")
        filepath = os.path.join(photo_folder, filename)
        photo_file.save(filepath)
        student_data['photo'] = filename
    else:
        student_data['photo'] = None

    # Insert into database
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Check if RFID already exists
        cur.execute("SELECT 1 FROM users WHERE rfid_code = ?", (student_data.get('rfid_code'),))
        if cur.fetchone():
            conn.close()
            return {"error": "RFID already exists in database"}, 400
        
        cur.execute("""
            INSERT INTO users (
                first_name, middle_name, last_name, age, gender, grade,
                section, contact, address, guardian, occupation, id_number, rfid_code, photo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            student_data.get('first_name'),
            student_data.get('middle_name'),
            student_data.get('last_name'),
            student_data.get('age'),
            student_data.get('gender'),
            student_data.get('grade'),
            student_data.get('section'),
            student_data.get('contact'),
            student_data.get('address'),
            student_data.get('guardian'),
            student_data.get('occupation', "Student"),
            student_data.get('id_number'),
            student_data.get('rfid_code'),
            student_data.get('photo')
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        return {"error": str(e)}, 500

    occupation = student_data.get('occupation', "Student")
    return {"message": f"{occupation} registered successfully!"}

@api_bp.route('/api/logs', methods=['GET'])
def get_logs():
    draw = int(request.args.get('draw', '1'))
    start = int(request.args.get('start', '0'))
    length = int(request.args.get('length', '10'))
    log_type = request.args.get('type', '').lower()
    search_value = request.args.get('search[value]', '').lower()

    conn = get_db_connection()
    cur = conn.cursor()

    # We will dynamically build WHERE conditions and parameters
    where_clauses = ["1=1"]
    params = []

    # filter by occupation (type)
    if log_type in ("student", "employee"):
        where_clauses.append("lower(occupation)=?")
        params.append(log_type)

    # search by text (first name / last name / occupation)
    if search_value:
        where_clauses.append("""(
            lower(first_name) LIKE ?
            OR lower(last_name) LIKE ?
            OR lower(middle_name) LIKE ?
            OR lower(occupation) LIKE ?
            OR lower(first_name || ' ' || last_name) LIKE ?
            OR lower(first_name || ' ' || middle_name || ' ' || last_name) LIKE ?
            OR lower(strftime('%b %d, %Y', substr(timestamp, 1, 10) || ' ' || substr(timestamp, 12, 8))) LIKE ?
            OR lower(strftime('%B %d, %Y', substr(timestamp, 1, 10) || ' ' || substr(timestamp, 12, 8))) LIKE ?
            OR lower(contact) LIKE ?
            OR lower(grade) LIKE ?
            OR lower(strandOrSec) LIKE ?
        )""")
        search_param = f"%{search_value}%"
        params += [search_param] * 11

    where_sql = " AND ".join(where_clauses)

    # total records (not filtered by search/type — for DataTables info)
    cur.execute("SELECT COUNT(*) FROM attendance")
    records_total = cur.fetchone()[0]

    # filtered count
    cur.execute(f"SELECT COUNT(*) FROM attendance WHERE {where_sql}", params)
    records_filtered = cur.fetchone()[0]

    # fetch actual data slice
    sql = f"""
        SELECT * FROM attendance
        WHERE {where_sql}
        ORDER BY timestamp DESC
        LIMIT ? OFFSET ?
    """
    final_params = params + [length, start]
    cur.execute(sql, final_params)

    rows = cur.fetchall()
    logs = [dict(r) for r in rows]

    # Build avatar URL
    for log in logs:
        photo = log.get("photo")
        log["avatar"] = url_for('api.get_student_photo', filename=photo, _external=True) if photo else None

    conn.close()

    return jsonify({
        "draw": draw,
        "recordsTotal": records_total,
        "recordsFiltered": records_filtered,
        "data": logs
    })

@api_bp.route('/api/students', methods=['GET'])
def get_students():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch students where occupation is 'student' OR occupation is NULL
    cursor.execute("""
        SELECT * FROM users WHERE occupation IS NULL OR LOWER(occupation) = 'student'
    """)
    rows = cursor.fetchall()

    # Convert DB rows to list of dicts
    student_list = []
    for row in rows:
        student = dict(row)
        
        # Attach avatar URLs if photo exists
        if student.get("photo"):
            student["avatar"] = url_for(
                'api.get_student_photo',
                filename=student["photo"],
                _external=True
            )
        else:
            student["avatar"] = None
        
        student_list.append(student)

    conn.close()
    return jsonify(student_list)

@api_bp.route('/api/students/<rfid>', methods=['DELETE'])
def delete_student_by_rfid(rfid):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if student exists
        cursor.execute("SELECT id, photo FROM users WHERE rfid_code = ?", (rfid,))
        student = cursor.fetchone()

        if not student:
            return jsonify({'error': 'Student not found'}), 404

        student_id, photo_filename = student

        # Delete the photo file if it exists
        if photo_filename:
            photo_dir = get_photo_folder_path()
            photo_full_path = os.path.join(photo_dir, photo_filename)
            if os.path.exists(photo_full_path):
                os.remove(photo_full_path)

        # Delete student record from DB
        cursor.execute("DELETE FROM users WHERE id = ?", (student_id,))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({'message': 'Student and photo deleted successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
 
@api_bp.route('/api/students/<rfid>', methods=['PUT'])
def update_student_by_rfid(rfid):
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400

    updated_data = request.get_json()

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch column names for SQLite
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]  # row[1] = column name

        updatable_fields = [col for col in columns if col != 'rfid_code']

        # Build query dynamically
        set_clauses = []
        values = []
        for key, value in updated_data.items():
            if key in updatable_fields:
                set_clauses.append(f"{key} = ?")
                values.append(value)

        if not set_clauses:
            return jsonify({'error': 'No valid fields to update'}), 400

        values.append(rfid)  # For WHERE condition

        sql = f"""
            UPDATE users
            SET {", ".join(set_clauses)}
            WHERE rfid_code = ?
        """
        cursor.execute(sql, values)
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({'error': 'Student not found'}), 404

        return jsonify({'message': 'Student updated successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@api_bp.route('/api/log', methods=['POST'])
def log_attendance():
    data = request.json
    rfid_code = data.get("rfid")
    if not rfid_code:
        return jsonify({"error": "RFID is required"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    # Load student/person from database instead of data.json
    cur.execute("""
        SELECT * FROM users 
        WHERE rfid_code = ?
        LIMIT 1
    """, (rfid_code,))
    matched = cur.fetchone()

    if not matched:
        conn.close()
        return jsonify({"error": "Student not found"}), 404

    # get last log for this rfid
    cur.execute("""
        SELECT * FROM attendance 
        WHERE rfid = ? 
        ORDER BY timestamp DESC 
        LIMIT 1
    """, (rfid_code,))
    last = cur.fetchone()

    now = datetime.now()
    today = now.date().isoformat()

    if last:
        last_dt = datetime.fromisoformat(last['timestamp'])
        last_date = last_dt.date().isoformat()

        if last_date == today:
            # SAME DAY
            if last['status'] == 'IN':
                status = 'OUT'
            else:
                conn.close()
                return jsonify({"error": "Already timed in/out today"}), 403
        else:
            # DIFFERENT DAY
            if last['status'] == 'IN':
                status = 'OUT'
            else:
                status = 'IN'
    else:
        status = 'IN'

    # Insert log entry into attendance table
    cur.execute("""
        INSERT INTO attendance
        (rfid, status, timestamp, first_name, middle_name, last_name, age, grade, strandOrSec, gender,
         guardian, occupation, id_number, contact, address, photo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        rfid_code, status, now.isoformat(),
        matched['first_name'],
        matched['middle_name'],
        matched['last_name'],
        matched['age'],
        matched['grade'],
        matched['section'],  # if DB column is strandOrSec, adjust this
        matched['gender'],
        matched['guardian'],
        matched['occupation'],
        matched['id_number'],
        matched['contact'],
        matched['address'],
        matched['photo']
    ))

    conn.commit()
    conn.close()

    return jsonify({"message": f"Log entry saved successfully as {status}", "status": status}), 200

@api_bp.route('/api/dashboard-stats', methods=['GET'])
def get_dashboard_stats():
    try:
        today_str = datetime.now().date().isoformat()
        conn = get_db_connection()
        cur = conn.cursor()

        # Count students
        cur.execute("SELECT COUNT(*) FROM users WHERE LOWER(occupation) = 'student'")
        total_students = cur.fetchone()[0]

        # Count employees
        cur.execute("SELECT COUNT(*) FROM users WHERE LOWER(occupation) = 'employee'")
        total_employees = cur.fetchone()[0]

        # Get today's logs
        cur.execute("""
            SELECT * FROM attendance
            WHERE timestamp LIKE ?
            ORDER BY timestamp DESC
        """, (today_str + "%",))
        today_logs = [dict(r) for r in cur.fetchall()]

        # Stats
        time_in_today = sum(1 for log in today_logs if log["status"] == "IN")
        time_out_today = sum(1 for log in today_logs if log["status"] == "OUT")
        present_today = len(set(log["rfid"] for log in today_logs if log["status"] == "IN"))

        # Most recent 3 logs
        recent_logs = today_logs[:3]

        conn.close()

        return jsonify({
            "total_students": total_students,
            "total_employees": total_employees,
            "present_today": present_today,
            "time_in_today": time_in_today,
            "time_out_today": time_out_today,
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

        new_in_dt = datetime.strptime(f"{date}T{time_in}", "%Y-%m-%dT%H:%M")
        if time_out:
            new_out_dt = datetime.strptime(f"{date}T{time_out}", "%Y-%m-%dT%H:%M")
            if new_out_dt <= new_in_dt:
                return jsonify({'error': 'Time out must be after time in'}), 400

        conn = get_db_connection()
        cur = conn.cursor()

        updated = False

        # update IN
        if original_time_in:
            cur.execute(
                "UPDATE attendance SET timestamp=? WHERE rfid=? AND timestamp=? AND status='IN'",
                (new_in_dt.isoformat(), rfid, original_time_in)
            )
            updated = updated or (cur.rowcount > 0)

        # update OUT
        if original_time_out and time_out:
            cur.execute(
                "UPDATE attendance SET timestamp=? WHERE rfid=? AND timestamp=? AND status='OUT'",
                (new_out_dt.isoformat(), rfid, original_time_out)
            )
            updated = updated or (cur.rowcount > 0)

        conn.commit()
        conn.close()

        if updated:
            return jsonify({'message': 'Attendance updated successfully'}), 200
        else:
            return jsonify({'error': 'No matching records found to update'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/api/check-rfid', methods=['POST'])
def check_rfid():
    data = request.get_json()
    if not data or 'rfid_code' not in data:
        return jsonify({"error": "RFID code is required"}), 400

    rfid_code = data['rfid_code']

    try:
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row  # Enables dictionary-like access
        cur = conn.cursor()

        # Search by rfid_code (case-insensitive)
        query = """
            SELECT * FROM users
            WHERE LOWER(rfid_code) = LOWER(?)
            LIMIT 1
        """
        cur.execute(query, (rfid_code,))
        student = cur.fetchone()

        cur.close()
        conn.close()

        if student:
            return jsonify({
                "exists": True,
                "student": dict(student),  # Convert sqlite Row to dict
                "message": "RFID found in database"
            })
        else:
            return jsonify({
                "exists": False,
                "message": "RFID not found in database"
            })

    except Exception as e:
        return jsonify({
            "error": str(e),
            "message": "Error checking RFID"
        }), 500

@api_bp.route('/api/admin-logout')
def admin_logout():
    resp = make_response(redirect(url_for('pages.admin_login')))
    resp.delete_cookie('admin_token')
    return resp