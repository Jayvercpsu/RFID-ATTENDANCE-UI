# db.py
import os
from utils.path_utils import get_app_data_dir

def get_db_path():
    folder = get_app_data_dir("RFID_ATTENDANCE")
    return os.path.join(folder, "attendance.db")

def get_db_connection():
    db_path = get_db_path()
    import sqlite3
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cur  = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rfid TEXT,
            status TEXT,
            timestamp TEXT,
            first_name TEXT, middle_name TEXT, last_name TEXT,
            age TEXT, grade TEXT, strandOrSec TEXT,
            gender TEXT, guardian TEXT, occupation TEXT,
            id_number TEXT, contact TEXT, address TEXT, photo TEXT
        )
    """)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("✅ Database created successfully.")
