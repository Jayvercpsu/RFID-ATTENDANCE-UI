from datetime import datetime
import os
import shutil
import zipfile
from db import get_db_name, get_db_path
from utils.path_utils import get_appdata_path


def create_backup_zip(backup_path: str) -> str:
    folders = ["CVE_PHOTO"]
    appdata = os.getenv('APPDATA', os.path.expanduser("~"))

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"rfid_backup_{timestamp}.zip"
    backup_full = os.path.join(backup_path, backup_filename)

    os.makedirs(backup_path, exist_ok=True)

    with zipfile.ZipFile(backup_full, 'w', zipfile.ZIP_DEFLATED) as z:
        # include folders
        for folder in folders:
            folder_path = os.path.join(appdata, folder)
            if os.path.exists(folder_path):
                for root, _, files in os.walk(folder_path):
                    for f in files:
                        file_path = os.path.join(root, f)
                        arcname = os.path.join(folder, os.path.relpath(file_path, folder_path))
                        z.write(file_path, arcname)

        # include the sqlite db
        db_path = get_db_path()
        if os.path.exists(db_path):
            z.write(db_path, arcname=get_db_name())

    return backup_full


def save_uploaded_backup(file) -> str:
    temp_dir = os.path.join(get_appdata_path(), 'rfid_temp')
    os.makedirs(temp_dir, exist_ok=True)

    filename = file.filename
    temp_zip_path = os.path.join(temp_dir, filename)
    file.save(temp_zip_path)
    return temp_zip_path, temp_dir

def extract_backup_zip(temp_zip_path: str, temp_dir: str) -> str:
    extract_path = os.path.join(temp_dir, 'extracted')
    # Clean up before extraction to avoid leftovers
    if os.path.exists(extract_path):
        shutil.rmtree(extract_path)
    with zipfile.ZipFile(temp_zip_path, 'r') as z:
        z.extractall(extract_path)
    return extract_path


def restore_backup_files(extract_path: str):
    appdata = get_appdata_path()
    for item in os.listdir(extract_path):
        src = os.path.join(extract_path, item)

        if item == get_db_name():
            dst_folder = os.path.join(appdata, "RFID_ATTENDANCE")
            os.makedirs(dst_folder, exist_ok=True)
            dst = os.path.join(dst_folder, get_db_name())
        else:
            dst = os.path.join(appdata, item)

        # Remove old files/folders
        if os.path.exists(dst):
            if os.path.isfile(dst):
                os.remove(dst)
            else:
                shutil.rmtree(dst)

        # Move new files/folders from extracted
        shutil.move(src, dst)


def cleanup_temp_dir(temp_dir: str):
    shutil.rmtree(temp_dir, ignore_errors=True)