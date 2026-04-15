import sqlite3
from werkzeug.security import generate_password_hash
from flask_login import UserMixin
from config import DATABASE

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT    UNIQUE NOT NULL,
            password   TEXT    NOT NULL,
            role       TEXT    NOT NULL CHECK(role IN ('admin', 'company', 'student')),
            is_active  INTEGER NOT NULL DEFAULT 1
        )
    """)

    # Create students table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER UNIQUE NOT NULL,
            full_name   TEXT    NOT NULL,
            email       TEXT    UNIQUE NOT NULL,
            phone       TEXT,
            department  TEXT,
            cgpa        REAL    DEFAULT 0.0,
            resume_path TEXT,
            created_at  TEXT    DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # Create companies table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER UNIQUE NOT NULL,
            company_name    TEXT    NOT NULL,
            hr_contact      TEXT,
            website         TEXT,
            description     TEXT,
            approval_status TEXT    NOT NULL DEFAULT 'Pending'
                            CHECK(approval_status IN ('Pending','Approved','Rejected')),
            is_blacklisted  INTEGER NOT NULL DEFAULT 0,
            created_at      TEXT    DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # Create placement_drives table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS placement_drives (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id           INTEGER NOT NULL,
            job_title            TEXT    NOT NULL,
            job_description      TEXT,
            eligibility_criteria TEXT,
            application_deadline TEXT    NOT NULL,
            salary               TEXT,
            location             TEXT,
            status               TEXT    NOT NULL DEFAULT 'Pending'
                                 CHECK(status IN ('Pending','Approved','Rejected','Closed')),
            created_at           TEXT    DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
        )
    """)

    # Create applications table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id  INTEGER NOT NULL,
            drive_id    INTEGER NOT NULL,
            applied_at  TEXT    DEFAULT CURRENT_TIMESTAMP,
            status      TEXT    NOT NULL DEFAULT 'Applied'
                        CHECK(status IN ('Applied','Shortlisted','Selected','Rejected')),
            remarks     TEXT,
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
            FOREIGN KEY (drive_id)   REFERENCES placement_drives(id) ON DELETE CASCADE,
            UNIQUE(student_id, drive_id)
        )
    """)

    # Seed admin only if not already present
    existing = cursor.execute(
        "SELECT id FROM users WHERE role = 'admin'"
    ).fetchone()

    if not existing:
        hashed = generate_password_hash('admin123')
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            ('admin', hashed, 'admin')
        )

    conn.commit()
    conn.close()

def get_user_by_id(user_id):
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    user = cursor.execute(
        "SELECT * FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()
    conn.close()

    if user:
        return User(user['id'], user['username'], user['role'], user['is_active'])
    return None

class User(UserMixin):
    def __init__(self, id, username, role, is_active):
        self.id = id
        self.username = username
        self.role = role
        self._active = is_active

    def get_id(self):
        return str(self.id)

    @property
    def is_active(self):
        return self._active == 1