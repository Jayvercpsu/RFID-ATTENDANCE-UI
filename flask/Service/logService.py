from datetime import datetime
from flask import jsonify, url_for
from Repository.logRepository import count_filtered_logs, count_total_logs, fetch_logs, find_last_attendance_log, get_attendance_logs_by_date, insert_attendance_log, update_attendance_timestamp
from Repository.userRepository import count_users_by_occupation, find_user_by_rfid
from db import get_db_connection


def get_logs_service(request_args):
    try:
        draw = int(request_args.get('draw', '1'))
        start = int(request_args.get('start', '0'))
        length = int(request_args.get('length', '10'))
        log_type = request_args.get('type', '').lower()
        search_value = request_args.get('search[value]', '').lower()

        where_clauses = ["1=1"]
        params = []

        if log_type in ("student", "employee"):
            where_clauses.append("lower(occupation)=?")
            params.append(log_type)

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

        conn = get_db_connection()
        records_total = count_total_logs(conn)
        records_filtered = count_filtered_logs(conn, where_sql, params)
        rows = fetch_logs(conn, where_sql, params, length, start)
        logs = [dict(row) for row in rows]

        for log in logs:
            photo = log.get("photo")
            log["avatar"] = url_for('api.get_student_photo', filename=photo, _external=True) if photo else None

        conn.close()

        return jsonify({
            "draw": draw,
            "recordsTotal": records_total,
            "recordsFiltered": records_filtered,
            "data": logs
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

def update_attendance_service(request):
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
        updated = False

        if original_time_in:
            updated_rows = update_attendance_timestamp(
                conn, rfid, new_in_dt.isoformat(), original_time_in, 'IN'
            )
            updated = updated or (updated_rows > 0)

        if original_time_out and time_out:
            updated_rows = update_attendance_timestamp(
                conn, rfid, new_out_dt.isoformat(), original_time_out, 'OUT'
            )
            updated = updated or (updated_rows > 0)

        conn.commit()
        conn.close()

        if updated:
            return jsonify({'message': 'Attendance updated successfully'}), 200
        else:
            return jsonify({'error': 'No matching records found to update'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

def log_attendance_service(request):
    try:
        data = request.json
        if not data or 'rfid' not in data:
            return jsonify({"error": "RFID is required"}), 400

        rfid_code = data['rfid']
        conn = get_db_connection()

        user = find_user_by_rfid(conn, rfid_code)
        if not user:
            conn.close()
            return jsonify({"error": "Student not found"}), 404

        last_log = find_last_attendance_log(conn, rfid_code)
        now = datetime.now()
        today = now.date().isoformat()

        if last_log:
            last_dt = datetime.fromisoformat(last_log['timestamp'])
            last_date = last_dt.date().isoformat()

            if last_date == today:
                # same day
                if last_log['status'] == 'IN':
                    status = 'OUT'
                else:
                    conn.close()
                    return jsonify({"error": "Already timed in/out today"}), 403
            else:
                # different day
                status = 'OUT' if last_log['status'] == 'IN' else 'IN'
        else:
            status = 'IN'

        insert_attendance_log(conn, rfid_code, status, now.isoformat(), user)
        conn.close()

        return jsonify({"message": f"Log entry saved successfully as {status}", "status": status}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

def get_dashboard_stats_service():
    try:
        today_str = datetime.now().date().isoformat()

        total_students = count_users_by_occupation('student')
        total_employees = count_users_by_occupation('employee')

        today_logs_rows = get_attendance_logs_by_date(today_str)
        today_logs = [dict(row) for row in today_logs_rows]

        time_in_today = sum(1 for log in today_logs if log.get("status") == "IN")
        time_out_today = sum(1 for log in today_logs if log.get("status") == "OUT")
        present_today = len(set(log["rfid"] for log in today_logs if log.get("status") == "IN"))

        recent_logs = today_logs[:3]

        return jsonify({
            "total_students": total_students,
            "total_employees": total_employees,
            "present_today": present_today,
            "time_in_today": time_in_today,
            "time_out_today": time_out_today,
            "recent_logs": recent_logs
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
