from datetime import datetime, timedelta
import bcrypt
from flask import Blueprint, make_response, redirect, request, jsonify, send_from_directory, url_for
import os
import json

import jwt
from db import get_db_connection
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
    data = request.json
    rfid_code = data.get("rfid")
    if not rfid_code:
        return jsonify({"error":"RFID is required"}),400

    # load student/person
    people_file_path = os.path.join(get_app_data_dir(), "data.json")
    if not os.path.exists(people_file_path):
        return jsonify({"error":"data.json not found"}),404

    with open(people_file_path,'r') as sf:
        content = sf.read().strip()
        people = json.loads(content) if content else []

    matched = next((s for s in people if s.get("rfid")==rfid_code or s.get("rfid_code")==rfid_code), None)
    if not matched:
        return jsonify({"error":"Student not found"}),404

    conn = get_db_connection()
    cur = conn.cursor()

    # get last log for this rfid
    cur.execute("SELECT * FROM attendance WHERE rfid=? ORDER BY timestamp DESC LIMIT 1", (rfid_code,))
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
                # last was OUT, so already timed in & out today
                return jsonify({"error":"Already timed in/out today"}),403
        else:
            # DIFFERENT DAY
            if last['status'] == 'IN':
                # forgot to OUT yesterday → treat now as OUT
                status = 'OUT'
            else:
                # last was OUT on previous day → new IN
                status = 'IN'
    else:
        # no history at all
        status = 'IN'

    cur.execute("""
        INSERT INTO attendance
        (rfid,status,timestamp,first_name,middle_name,last_name,age,grade,strandOrSec,gender,
         guardian,occupation,id_number,contact,address,photo)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        rfid_code, status, now.isoformat(),
        matched.get("first_name",""),
        matched.get("middle_name",""),
        matched.get("last_name",""),
        matched.get("age",""),
        matched.get("grade",""),
        matched.get("section",""),
        matched.get("gender",""),
        matched.get("guardian",""),
        matched.get("occupation",""),
        matched.get("id_number",""),
        matched.get("contact",""),
        matched.get("address",""),
        matched.get("photo","")
    ))
    conn.commit()
    conn.close()

    return jsonify({"message": f"Log entry saved successfully as {status}","status":status}),200

@api_bp.route('/api/dashboard-stats', methods=['GET'])
def get_dashboard_stats():
    try:
        # Load master data.json
        student_file = os.path.join(get_app_data_dir(), "data.json")
        with open(student_file, 'r') as sf:
            students = json.load(sf)

        # Load TODAY's attendance logs from SQLite
        today_str = datetime.now().date().isoformat()
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM attendance WHERE timestamp LIKE ? ORDER BY timestamp DESC", (today_str + "%",))
        today_logs = [dict(r) for r in cur.fetchall()]
        conn.close()

        # Totals
        total_students  = len([s for s in students if s.get("occupation", "").lower() == "student"])
        total_employees = len([s for s in students if s.get("occupation", "").lower() == "employee"])

        # Stats
        time_in_today  = len([log for log in today_logs if log["status"] == "IN"])
        time_out_today = len([log for log in today_logs if log["status"] == "OUT"])
        present_today  = len(set(log["rfid"] for log in today_logs if log["status"] == "IN"))

        # Most recent 3 logs for dashboard
        recent_logs = today_logs[:3]

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

    if not os.path.exists(STUDENT_FILE):
        return jsonify({"exists": False, "message": "Database not found"}), 404

    try:
        with open(STUDENT_FILE, 'r') as f:
            students = json.load(f)

        exists = any(
            str(student.get('rfid', '')).lower() == str(rfid_code).lower() or 
            str(student.get('rfid_code', '')).lower() == str(rfid_code).lower()
            for student in students
        )

        if exists:
            student = next(
                s for s in students 
                if (str(s.get('rfid', '')).lower() == str(rfid_code).lower() or 
                   (str(s.get('rfid_code', '')).lower() == str(rfid_code).lower()
            )))
            
            return jsonify({
                "exists": True,
                "student": student,
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