import os
from sqlite3 import Connection
from db import get_db_connection
from utils.path_utils import get_photo_folder_path
from werkzeug.utils import secure_filename

def fetch_photo_file(filename: str):
    # Just return the photo folder path
    return get_photo_folder_path()


def save_student_photo(photo_file, rfid_code):
    photo_folder = get_photo_folder_path()
    os.makedirs(photo_folder, exist_ok=True)
    filename = secure_filename(f"{rfid_code}.jpg")
    filepath = os.path.join(photo_folder, filename)
    photo_file.save(filepath)
    return filename


def check_rfid_exists(rfid_code):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE rfid_code = ?", (rfid_code,))
    exists = cur.fetchone() is not None
    conn.close()
    return exists


def insert_student(student_data):
    conn = get_db_connection()
    cur = conn.cursor()
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


def find_student_by_rfid(rfid):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, photo FROM users WHERE rfid_code = ?", (rfid,))
    student = cur.fetchone()
    conn.close()
    return student


def delete_photo_file(photo_filename):
    if not photo_filename:
        return
    photo_dir = get_photo_folder_path()
    photo_full_path = os.path.join(photo_dir, photo_filename)
    if os.path.exists(photo_full_path):
        os.remove(photo_full_path)


def delete_student_by_id(student_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id = ?", (student_id,))
    conn.commit()
    conn.close()


def get_user_table_columns():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cur.fetchall()]  # row[1] = column name
    conn.close()
    return columns


def update_student_by_rfid(rfid, update_fields: dict):
    conn = get_db_connection()
    cur = conn.cursor()

    set_clauses = []
    values = []

    for key, value in update_fields.items():
        set_clauses.append(f"{key} = ?")
        values.append(value)

    values.append(rfid)  # for WHERE clause

    sql = f"""
        UPDATE users
        SET {", ".join(set_clauses)}
        WHERE rfid_code = ?
    """

    cur.execute(sql, values)
    conn.commit()
    rowcount = cur.rowcount

    cur.close()
    conn.close()

    return rowcount  # number of updated rows


def count_users_by_occupation(occupation):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users WHERE LOWER(occupation) = ?", (occupation.lower(),))
    count = cur.fetchone()[0]
    conn.close()
    return count


def find_user_by_rfid(conn: Connection, rfid_code):
    cur = conn.cursor()
    query = """
        SELECT * FROM users
        WHERE LOWER(rfid_code) = LOWER(?)
        LIMIT 1
    """
    cur.execute(query, (rfid_code,))
    user = cur.fetchone()
    return user


def fetch_students():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM users WHERE occupation IS NULL OR LOWER(occupation) = 'student'
    """)
    rows = cur.fetchall()
    conn.close()
    return rows