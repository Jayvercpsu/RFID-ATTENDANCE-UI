from functools import wraps
from flask import redirect, request, jsonify, url_for
import jwt

SECRET_KEY = "CVE_SECRET_KEY"

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"message": "Token missing!"}), 401

        try:
            jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token expired!"}), 401
        except Exception:
            return jsonify({"message": "Token is invalid"}), 401

        return f(*args, **kwargs)
    return decorated

def login_required_page(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('admin_token')
        if not token:
            return redirect(url_for('pages.admin_login'))

        try:
            jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return redirect(url_for('pages.admin_login'))
        except Exception:
            return redirect(url_for('pages.admin_login'))

        return f(*args, **kwargs)
    return decorated
