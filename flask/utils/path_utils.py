# utils/path_utils.py
import os

def get_app_data_dir(app_name="jpa_profile"):
    base_dir = os.getenv("APPDATA", os.path.expanduser("~"))
    app_data_dir = os.path.join(base_dir, app_name)

    if not os.path.exists(app_data_dir):
        os.makedirs(app_data_dir)

    return app_data_dir
