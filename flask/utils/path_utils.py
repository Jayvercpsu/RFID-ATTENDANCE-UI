# utils/path_utils.py
import os
import json
import bcrypt

APP_NAME = "RFID_CREDENTIALS"

# Location of your default admin.json (inside project dir, read-only)
DEFAULT_ADMIN_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "credentials",
    "admin.json"
)

def get_app_data_dir(app_name="CVE_REGISTER"):
    base_dir = os.getenv("APPDATA", os.path.expanduser("~"))
    app_data_dir = os.path.join(base_dir, app_name)

    if not os.path.exists(app_data_dir):
        os.makedirs(app_data_dir)

    return app_data_dir

def get_photo_folder_path():
    path = os.path.join(os.getenv("APPDATA", os.path.expanduser("~")), "CVE_PHOTO")
    os.makedirs(path, exist_ok=True)
    return path

# Location of the user’s editable credentials.json in APPDATA
def get_appdata_cred_path():
    appdata = os.getenv("APPDATA", os.path.expanduser("~"))
    cred_dir = os.path.join(appdata, APP_NAME, "credentials")
    os.makedirs(cred_dir, exist_ok=True)
    return os.path.join(cred_dir, "credentials.json")


def load_admin():
    """Loads credentials from APPDATA, and if not present, copy defaults there"""
    cred_path = get_appdata_cred_path()

    # If not exists → copy default bundle file first
    if not os.path.exists(cred_path):
        with open(DEFAULT_ADMIN_PATH, "r") as f:
            default_data = json.load(f)

        # Hash default password for the stored version
        hashed_pw = bcrypt.hashpw(default_data["password"].encode(), bcrypt.gensalt()).decode()
        default_data["password"] = hashed_pw

        with open(cred_path, "w") as f:
            json.dump(default_data, f, indent=2)

    # Load and return
    with open(cred_path, "r") as f:
        return json.load(f)


def save_admin(new_data):
    """Save new credentials into APPDATA (password will be hashed if plaintext given)"""
    cred_path = get_appdata_cred_path()

    # If password was updated in plaintext → hash before saving
    if "password" in new_data and not new_data["password"].startswith("$2b$"):
        new_data["password"] = bcrypt.hashpw(new_data["password"].encode(), bcrypt.gensalt()).decode()

    with open(cred_path, "w") as f:
        json.dump(new_data, f, indent=2)