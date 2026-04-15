from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from helpers import get_db

auth_bp = Blueprint('auth', __name__, template_folder='templates')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect_based_on_role()

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()
        conn.close()

        if not user:
            flash('Invalid credentials', 'error')
            return render_template('auth/login.html')

        if not check_password_hash(user['password'], password):
            flash('Invalid credentials', 'error')
            return render_template('auth/login.html')

        if user['is_active'] == 0:
            flash('Your account has been deactivated', 'error')
            return render_template('auth/login.html')

        if user['role'] == 'company':
            conn = get_db()
            company = conn.execute(
                "SELECT * FROM companies WHERE user_id = ?",
                (user['id'],)
            ).fetchone()
            conn.close()

            if company:
                if company['approval_status'] != 'Approved':
                    flash('Your company account is pending admin approval', 'error')
                    return render_template('auth/login.html')
                if company['is_blacklisted'] == 1:
                    flash('Your company account has been blacklisted', 'error')
                    return render_template('auth/login.html')

        from helpers import User
        user_obj = User(user['id'], user['username'], user['role'], user['is_active'])
        login_user(user_obj)

        return redirect_based_on_role()

    return render_template('auth/login.html')

def redirect_based_on_role():
    if current_user.role == 'admin':
        return redirect(url_for('admin.dashboard'))
    elif current_user.role == 'company':
        return redirect(url_for('company.dashboard'))
    else:
        return redirect(url_for('student.dashboard'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect_based_on_role()

    if request.method == 'POST':
        role = request.form['role']
        username = request.form['username']
        password = request.form['password']

        conn = get_db()

        # Check if username already exists
        existing_user = conn.execute(
            "SELECT id FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        if existing_user:
            flash('Username already taken', 'error')
            conn.close()
            return render_template('auth/register.html')

        from werkzeug.security import generate_password_hash
        hashed_password = generate_password_hash(password)

        if role == 'student':
            # Insert into users table
            cursor = conn.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (username, hashed_password, 'student')
            )
            user_id = cursor.lastrowid

            cgpa_str = request.form.get('cgpa', '').strip()
            cgpa_val = float(cgpa_str) if cgpa_str else 0.0

            # Insert into students table
            conn.execute(
                "INSERT INTO students (user_id, full_name, email, phone, department, cgpa) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, request.form['full_name'], request.form['email'],
                 request.form.get('phone', ''), request.form.get('department', ''),
                 cgpa_val)
            )

            conn.commit()
            conn.close()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))

        elif role == 'company':
            # Insert into users table
            cursor = conn.execute(
                "INSERT INTO users (username, password, role, is_active) VALUES (?, ?, ?, 1)",
                (username, hashed_password, 'company')
            )
            user_id = cursor.lastrowid

            # Insert into companies table
            conn.execute(
                """INSERT INTO companies (user_id, company_name, hr_contact, website, description, approval_status)
                   VALUES (?, ?, ?, ?, ?, 'Pending')""",
                (user_id, request.form['company_name'], request.form.get('hr_contact', ''),
                 request.form.get('website', ''), request.form.get('description', ''))
            )

            conn.commit()
            conn.close()
            flash('Registration submitted. Await admin approval.', 'success')
            return redirect(url_for('auth.login'))

    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))