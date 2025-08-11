import os
import sys
from faker import Faker

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db import get_db_connection, init_db

def seed_fake_users(count=10):
    fake = Faker()
    conn = get_db_connection()
    cur = conn.cursor()

    for _ in range(count):
        rfid_code = fake.unique.bothify(text='RFID###??')  # e.g. RFID123AB
        first_name = fake.first_name()
        middle_name = fake.first_name()
        last_name = fake.last_name()
        age = str(fake.random_int(min=15, max=25))
        gender = fake.random_element(elements=('Male', 'Female'))
        grade = str(fake.random_int(min=7, max=12))
        section = fake.random_uppercase_letter()
        contact = fake.phone_number()
        address = fake.address().replace('\n', ', ')
        guardian = fake.name()
        occupation = fake.random_element(elements=["Student", "Employee"])
        id_number = fake.unique.bothify(text='S######')
        photo = None  # You can leave None or add logic for dummy photo filename

        # Check if RFID exists before insert (just in case)
        cur.execute("SELECT 1 FROM users WHERE rfid_code = ?", (rfid_code,))
        if cur.fetchone():
            print(f"RFID {rfid_code} already exists. Skipping...")
            continue

        cur.execute("""
            INSERT INTO users (
                first_name, middle_name, last_name, age, gender, grade,
                section, contact, address, guardian, occupation,
                id_number, rfid_code, photo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            first_name, middle_name, last_name, age, gender,
            grade, section, contact, address, guardian,
            occupation, id_number, rfid_code, photo
        ))

        # Print the seeded user info
        print(f"Seeded user: {first_name} {middle_name} {last_name} | RFID: {rfid_code} | Occupation: {occupation}")

    conn.commit()
    conn.close()
    print(f"✅ {count} dummy users seeded successfully.")


if __name__ == "__main__":
    init_db()
    seed_fake_users(20)
