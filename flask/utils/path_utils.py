# utils/path_utils.py
import os
import json

def get_app_data_dir(app_name="CVE_REGISTER"):
    base_dir = os.getenv("APPDATA", os.path.expanduser("~"))
    app_data_dir = os.path.join(base_dir, app_name)

    if not os.path.exists(app_data_dir):
        os.makedirs(app_data_dir)

    return app_data_dir

def get_student_file_path(filename="logs.json"):
    """
    Returns the full path to the logs.json file (or any given filename)
    inside the CVE_ATTENDANCE app data directory.
    Ensures the directory exists.
    """
    app_folder = get_app_data_dir("CVE_ATTENDANCE")
    return os.path.join(app_folder, filename)

def get_photo_folder_path():
    path = os.path.join(os.getenv("APPDATA", os.path.expanduser("~")), "CVE_PHOTO")
    os.makedirs(path, exist_ok=True)
    return path