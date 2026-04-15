from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from helpers import get_db, role_required, save_resume
from werkzeug.utils import secure_filename
from datetime import datetime
import os

student_bp = Blueprint('student', __name__, template_folder='templates')

def get_current_student():
    conn = get_db()
    student = conn.execute(
        "SELECT * FROM students WHERE user_id = ?",
        (current_user.id,)
    ).fetchone()
    conn.close()
    return student

@student_bp.route('/dashboard')
@login_required
@role_required('student')
def dashboard():
    student = get_current_student()
    conn = get_db()

    # Get approved drives that student hasn't applied to yet
    open_drives = conn.execute(
        """SELECT pd.*, c.company_name
           FROM placement_drives pd
           JOIN companies c ON pd.company_id = c.id
           WHERE pd.status = 'Approved'
             AND pd.application_deadline >= DATE('now')
             AND pd.id NOT IN (
                 SELECT drive_id FROM applications WHERE student_id = ?
             )
           ORDER BY pd.application_deadline ASC""",
        (student['id'],)
    ).fetchall()

    # Get student's active applications
    applications = conn.execute(
        """SELECT a.*, pd.job_title, c.company_name, pd.application_deadline
           FROM applications a
           JOIN placement_drives pd ON a.drive_id = pd.id
           JOIN companies c ON pd.company_id = c.id
           WHERE a.student_id = ?
           ORDER BY a.applied_at DESC""",
        (student['id'],)
    ).fetchall()

    conn.close()

    return render_template('student/dashboard.html',
                         student=student,
                         open_drives=open_drives,
                         applications=applications)

@student_bp.route('/drive/<int:id>')
@login_required
@role_required('student')
def drive_detail(id):
    student = get_current_student()
    conn = get_db()

    # Get drive details
    drive = conn.execute(
        """SELECT pd.*, c.company_name, c.website, c.description AS company_desc
           FROM placement_drives pd
           JOIN companies c ON pd.company_id = c.id
           WHERE pd.id = ? AND pd.status = 'Approved'""",
        (id,)
    ).fetchone()

    if not drive:
        conn.close()
        abort(404)

    # Check if student has already applied
    already_applied = conn.execute(
        "SELECT id FROM applications WHERE student_id = ? AND drive_id = ?",
        (student['id'], id)
    ).fetchone() is not None

    # Check if deadline has passed
    deadline_passed = datetime.strptime(drive['application_deadline'], '%Y-%m-%d') < datetime.now()

    conn.close()

    return render_template('student/drive_detail.html',
                         drive=drive,
                         already_applied=already_applied,
                         deadline_passed=deadline_passed,
                         student=student)

@student_bp.route('/drive/<int:id>/apply', methods=['POST'])
@login_required
@role_required('student')
def apply_drive(id):
    student = get_current_student()
    conn = get_db()

    # Get drive details
    drive = conn.execute(
        "SELECT * FROM placement_drives WHERE id = ?",
        (id,)
    ).fetchone()

    if not drive:
        conn.close()
        flash('Drive not found', 'error')
        return redirect(url_for('student.dashboard'))

    # Check if drive is approved
    if drive['status'] != 'Approved':
        conn.close()
        flash('This drive is not currently accepting applications', 'error')
        return redirect(url_for('student.dashboard'))

    # Check if deadline has passed
    if datetime.strptime(drive['application_deadline'], '%Y-%m-%d') < datetime.now():
        conn.close()
        flash('Application deadline has passed', 'error')
        return redirect(url_for('student.drive_detail', id=id))

    # Check if student has already applied
    existing = conn.execute(
        "SELECT id FROM applications WHERE student_id = ? AND drive_id = ?",
        (student['id'], id)
    ).fetchone()

    if existing:
        conn.close()
        flash('You have already applied to this drive', 'error')
        return redirect(url_for('student.drive_detail', id=id))

    # Apply to the drive
    conn.execute(
        "INSERT INTO applications (student_id, drive_id, status) VALUES (?, ?, 'Applied')",
        (student['id'], id)
    )

    conn.commit()
    conn.close()

    flash('Application submitted successfully', 'success')
    return redirect(url_for('student.dashboard'))

@student_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@role_required('student')
def profile():
    student = get_current_student()
    conn = get_db()

    if request.method == 'POST':
        cgpa_str = request.form.get('cgpa', '').strip()
        cgpa_val = float(cgpa_str) if cgpa_str else 0.0

        # Update student profile
        conn.execute(
            """UPDATE students
               SET full_name = ?, email = ?, phone = ?, department = ?, cgpa = ?
               WHERE user_id = ?""",
            (request.form['full_name'], request.form['email'], request.form.get('phone', ''),
             request.form.get('department', ''), cgpa_val, current_user.id)
        )

        # Handle resume upload if file is present
        if 'resume' in request.files:
            file = request.files['resume']
            if file and file.filename:
                from config import UPLOAD_FOLDER
                if not os.path.exists(UPLOAD_FOLDER):
                    os.makedirs(UPLOAD_FOLDER)

                # Save resume
                resume_path = save_resume(file, student['id'])
                if resume_path:
                    conn.execute(
                        "UPDATE students SET resume_path = ? WHERE id = ?",
                        (resume_path, student['id'])
                    )

        conn.commit()
        conn.close()

        flash('Profile updated successfully', 'success')
        return redirect(url_for('student.profile'))

    conn.close()
    return render_template('student/profile.html', student=student)

@student_bp.route('/history')
@login_required
@role_required('student')
def history():
    student = get_current_student()
    conn = get_db()

    applications = conn.execute(
        """SELECT a.*,
                  pd.job_title, pd.location, pd.salary,
                  c.company_name,
                  a.applied_at, a.status, a.remarks
           FROM applications a
           JOIN placement_drives pd ON a.drive_id = pd.id
           JOIN companies c ON pd.company_id = c.id
           WHERE a.student_id = ?
           ORDER BY a.applied_at DESC""",
        (student['id'],)
    ).fetchall()

    conn.close()

    return render_template('student/history.html', applications=applications)