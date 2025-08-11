from sqlite3 import Connection
from db import get_db_connection


def count_total_logs(conn: Connection):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM attendance")
    return cur.fetchone()[0]


def count_filtered_logs(conn: Connection, where_sql, params):
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM attendance WHERE {where_sql}", params)
    return cur.fetchone()[0]


def fetch_logs(conn: Connection, where_sql, params, length, start):
    cur = conn.cursor()
    sql = f"""
        SELECT * FROM attendance
        WHERE {where_sql}
        ORDER BY timestamp DESC
        LIMIT ? OFFSET ?
    """
    final_params = params + [length, start]
    cur.execute(sql, final_params)
    return cur.fetchall()


def get_attendance_logs_by_date(date_str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM attendance
        WHERE timestamp LIKE ?
        ORDER BY timestamp DESC
    """, (date_str + "%",))
    logs = cur.fetchall()
    conn.close()
    return logs


def find_last_attendance_log(conn: Connection, rfid_code: str):
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM attendance 
        WHERE rfid = ? 
        ORDER BY timestamp DESC 
        LIMIT 1
    """, (rfid_code,))
    last_log = cur.fetchone()
    cur.close()
    return last_log


def update_attendance_timestamp(conn: Connection, rfid, new_timestamp, original_timestamp, status):
    cur = conn.cursor()
    cur.execute(
        "UPDATE attendance SET timestamp=? WHERE rfid=? AND timestamp=? AND status=?",
        (new_timestamp, rfid, original_timestamp, status)
    )
    updated_rows = cur.rowcount
    cur.close()
    return updated_rows


def insert_attendance_log(conn: Connection, rfid_code: str, status: str, now_iso: str, user: dict):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO attendance
        (rfid, status, timestamp, first_name, middle_name, last_name, age, grade, strandOrSec, gender,
         guardian, occupation, id_number, contact, address, photo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        rfid_code, status, now_iso,
        user['first_name'],
        user['middle_name'],
        user['last_name'],
        user['age'],
        user['grade'],
        user['section'],  # adjust if column name is strandOrSec
        user['gender'],
        user['guardian'],
        user['occupation'],
        user['id_number'],
        user['contact'],
        user['address'],
        user['photo']
    ))
    conn.commit()
    cur.close()


