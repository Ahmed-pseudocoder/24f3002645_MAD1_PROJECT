from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from helpers import get_db, role_required, save_resume
from datetime import datetime

company_bp = Blueprint('company', __name__, template_folder='templates')

def get_current_company():
    conn = get_db()
    company = conn.execute(
        "SELECT * FROM companies WHERE user_id = ?",
        (current_user.id,)
    ).fetchone()
    conn.close()
    return company

@company_bp.route('/dashboard')
@login_required
@role_required('company')
def dashboard():
    company = get_current_company()

    if not company or company['approval_status'] != 'Approved':
        flash('Your company account is pending admin approval', 'error')
        return redirect(url_for('company.dashboard'))

    conn = get_db()

    # Get company's drives with applicant count
    drives = conn.execute(
        """SELECT pd.*,
                  (SELECT COUNT(*) FROM applications WHERE drive_id = pd.id) AS applicant_count
           FROM placement_drives pd
           WHERE pd.company_id = ?
           ORDER BY pd.created_at DESC""",
        (company['id'],)
    ).fetchall()

    conn.close()

    return render_template('company/dashboard.html', company=company, drives=drives)

@company_bp.route('/drive/create', methods=['GET', 'POST'])
@login_required
@role_required('company')
def create_drive():
    company = get_current_company()

    if not company or company['approval_status'] != 'Approved':
        flash('Your company account is pending admin approval', 'error')
        return redirect(url_for('company.dashboard'))

    if request.method == 'POST':
        conn = get_db()

        conn.execute(
            """INSERT INTO placement_drives
               (company_id, job_title, job_description, eligibility_criteria,
                application_deadline, salary, location, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending')""",
            (company['id'], request.form['job_title'], request.form['job_description'],
             request.form['eligibility_criteria'], request.form['application_deadline'],
             request.form['salary'], request.form['location'])
        )

        conn.commit()
        conn.close()

        flash('Drive submitted for admin approval.', 'success')
        return redirect(url_for('company.dashboard'))

    return render_template('company/create_drive.html')

@company_bp.route('/drive/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('company')
def edit_drive(id):
    company = get_current_company()
    conn = get_db()

    # Check if drive exists and belongs to this company
    drive = conn.execute(
        "SELECT * FROM placement_drives WHERE id = ? AND company_id = ?",
        (id, company['id'])
    ).fetchone()

    if not drive:
        conn.close()
        abort(404)

    # Check if drive is closed
    if drive['status'] == 'Closed':
        conn.close()
        flash('Cannot edit a closed drive', 'error')
        return redirect(url_for('company.dashboard'))

    if request.method == 'POST':
        conn.execute(
            """UPDATE placement_drives
               SET job_title = ?, job_description = ?, eligibility_criteria = ?,
                   application_deadline = ?, salary = ?, location = ?, status = 'Pending'
               WHERE id = ? AND company_id = ?""",
            (request.form['job_title'], request.form['job_description'],
             request.form['eligibility_criteria'], request.form['application_deadline'],
             request.form['salary'], request.form['location'], id, company['id'])
        )

        conn.commit()
        conn.close()

        flash('Drive updated and resubmitted for approval.', 'success')
        return redirect(url_for('company.dashboard'))

    conn.close()
    return render_template('company/edit_drive.html', drive=drive)

@company_bp.route('/drive/<int:id>/delete', methods=['POST'])
@login_required
@role_required('company')
def delete_drive(id):
    company = get_current_company()
    conn = get_db()

    # Check if drive exists and belongs to this company
    conn.execute(
        "DELETE FROM placement_drives WHERE id = ? AND company_id = ?",
        (id, company['id'])
    )

    conn.commit()
    conn.close()

    flash('Drive deleted successfully', 'success')
    return redirect(url_for('company.dashboard'))

@company_bp.route('/drive/<int:id>/close', methods=['POST'])
@login_required
@role_required('company')
def close_drive(id):
    company = get_current_company()
    conn = get_db()

    # Check if drive exists and belongs to this company
    conn.execute(
        "UPDATE placement_drives SET status = 'Closed' WHERE id = ? AND company_id = ?",
        (id, company['id'])
    )

    conn.commit()
    conn.close()

    flash('Drive closed successfully', 'success')
    return redirect(url_for('company.dashboard'))

@company_bp.route('/drive/<int:id>/applications')
@login_required
@role_required('company')
def view_applications(id):
    company = get_current_company()
    conn = get_db()

    # Check if drive exists and belongs to this company
    drive = conn.execute(
        "SELECT * FROM placement_drives WHERE id = ? AND company_id = ?",
        (id, company['id'])
    ).fetchone()

    if not drive:
        conn.close()
        abort(404)

    # Get applications with student details
    applications = conn.execute(
        """SELECT a.*, s.full_name, s.email, s.phone, s.department,
                  s.cgpa, s.resume_path
           FROM applications a
           JOIN students s ON a.student_id = s.id
           WHERE a.drive_id = ?
           ORDER BY a.applied_at DESC""",
        (id,)
    ).fetchall()

    conn.close()

    return render_template('company/applications.html', drive=drive, applications=applications)

@company_bp.route('/application/<int:id>/update', methods=['POST'])
@login_required
@role_required('company')
def update_application(id):
    company = get_current_company()
    conn = get_db()

    # Update application status
    conn.execute(
        """UPDATE applications
           SET status = ?, remarks = ?
           WHERE id = ?
             AND drive_id IN (SELECT id FROM placement_drives WHERE company_id = ?)""",
        (request.form['status'], request.form.get('remarks', ''), id, company['id'])
    )

    conn.commit()
    conn.close()

    flash('Application status updated successfully', 'success')
    return redirect(url_for('company.view_applications', id=request.form['drive_id']))