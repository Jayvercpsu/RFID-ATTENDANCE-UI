# utils/path_utils.py
import os

def get_app_data_dir(app_name="CVE_REGISTER"):
    base_dir = os.getenv("APPDATA", os.path.expanduser("~"))
    app_data_dir = os.path.join(base_dir, app_name)

    if not os.path.exists(app_data_dir):
        os.makedirs(app_data_dir)

    return app_data_dir

def get_student_file_path():
    base_dir = os.getenv("APPDATA", os.path.expanduser("~"))  # default to user folder
    app_folder = os.path.join(base_dir, "CVE_ATTENDANCE")
    os.makedirs(app_folder, exist_ok=True)

    return os.path.join(app_folder, "logs.json")
