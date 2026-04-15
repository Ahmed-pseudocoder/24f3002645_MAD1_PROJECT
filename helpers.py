import sqlite3
import os
from flask_login import UserMixin
from functools import wraps
from flask import abort
from flask_login import current_user
from werkzeug.utils import secure_filename
from config import DATABASE, UPLOAD_FOLDER, ALLOWED_EXTENSIONS

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row   # access columns by name: row['full_name']
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

class User(UserMixin):
    def __init__(self, id, username, role, is_active):
        self.id        = id
        self.username  = username
        self.role      = role
        self._active   = is_active

    def get_id(self):
        return str(self.id)

    @property
    def is_active(self):
        return self._active == 1

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated
    return decorator

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_resume(file, student_id):
    if file and allowed_file(file.filename):
        ext      = file.filename.rsplit('.', 1)[1].lower()
        filename = secure_filename(f"student_{student_id}.{ext}")
        path     = os.path.join(UPLOAD_FOLDER, filename)
        file.save(path)
        return path
    return None

def load_user(user_id):
    from models import get_user_by_id
    return get_user_by_id(user_id)