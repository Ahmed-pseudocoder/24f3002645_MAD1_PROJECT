from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from helpers import get_db, role_required

admin_bp = Blueprint('admin', __name__, template_folder='templates')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    conn = get_db()

    # Get counts
    student_count = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    approved_company_count = conn.execute(
        "SELECT COUNT(*) FROM companies WHERE approval_status = 'Approved'"
    ).fetchone()[0]
    drive_count = conn.execute("SELECT COUNT(*) FROM placement_drives").fetchone()[0]
    application_count = conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0]

    # Pending company approvals
    pending_companies = conn.execute(
        "SELECT c.*, u.username FROM companies c "
        "JOIN users u ON c.user_id = u.id "
        "WHERE c.approval_status = 'Pending' "
        "ORDER BY c.created_at DESC"
    ).fetchall()

    # Pending drives
    pending_drives = conn.execute(
        "SELECT pd.*, c.company_name FROM placement_drives pd "
        "JOIN companies c ON pd.company_id = c.id "
        "WHERE pd.status = 'Pending' "
        "ORDER BY pd.created_at DESC"
    ).fetchall()

    conn.close()

    return render_template('admin/dashboard.html',
                         student_count=student_count,
                         approved_company_count=approved_company_count,
                         drive_count=drive_count,
                         application_count=application_count,
                         pending_companies=pending_companies,
                         pending_drives=pending_drives)

@admin_bp.route('/companies')
@admin_required
def companies():
    conn = get_db()
    companies = conn.execute(
        "SELECT c.*, u.username, u.is_active "
        "FROM companies c "
        "JOIN users u ON c.user_id = u.id "
        "ORDER BY c.created_at DESC"
    ).fetchall()
    conn.close()
    return render_template('admin/companies.html', companies=companies)

@admin_bp.route('/company/<int:id>/approve', methods=['POST'])
@admin_required
def approve_company(id):
    conn = get_db()
    conn.execute("UPDATE companies SET approval_status = 'Approved' WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash('Company approved successfully', 'success')
    return redirect(url_for('admin.companies'))

@admin_bp.route('/company/<int:id>/reject', methods=['POST'])
@admin_required
def reject_company(id):
    conn = get_db()
    conn.execute("UPDATE companies SET approval_status = 'Rejected' WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash('Company rejected successfully', 'success')
    return redirect(url_for('admin.companies'))

@admin_bp.route('/company/<int:id>/blacklist', methods=['POST'])
@admin_required
def blacklist_company(id):
    conn = get_db()

    # Get user_id from company
    user_id = conn.execute(
        "SELECT user_id FROM companies WHERE id = ?", (id,)
    ).fetchone()['user_id']

    # Blacklist company and deactivate user
    conn.execute("UPDATE companies SET is_blacklisted = 1 WHERE id = ?", (id,))
    conn.execute("UPDATE users SET is_active = 0 WHERE id = ?", (user_id,))

    # Close all drives for this company
    conn.execute("UPDATE placement_drives SET status = 'Closed' WHERE company_id = ?", (id,))

    conn.commit()
    conn.close()
    flash('Company blacklisted successfully', 'success')
    return redirect(url_for('admin.companies'))

@admin_bp.route('/company/<int:id>/delete', methods=['POST'])
@admin_required
def delete_company(id):
    conn = get_db()
    user_id = conn.execute(
        "SELECT user_id FROM companies WHERE id = ?", (id,)
    ).fetchone()['user_id']
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    flash('Company deleted successfully', 'success')
    return redirect(url_for('admin.companies'))

@admin_bp.route('/students')
@admin_required
def students():
    conn = get_db()
    students = conn.execute(
        "SELECT s.*, u.username, u.is_active "
        "FROM students s "
        "JOIN users u ON s.user_id = u.id "
        "ORDER BY s.created_at DESC"
    ).fetchall()
    conn.close()
    return render_template('admin/students.html', students=students)

@admin_bp.route('/student/<int:id>/blacklist', methods=['POST'])
@admin_required
def blacklist_student(id):
    conn = get_db()
    user_id = conn.execute(
        "SELECT user_id FROM students WHERE id = ?", (id,)
    ).fetchone()['user_id']
    conn.execute("UPDATE users SET is_active = 0 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    flash('Student blacklisted successfully', 'success')
    return redirect(url_for('admin.students'))

@admin_bp.route('/student/<int:id>/activate', methods=['POST'])
@admin_required
def activate_student(id):
    conn = get_db()
    user_id = conn.execute(
        "SELECT user_id FROM students WHERE id = ?", (id,)
    ).fetchone()['user_id']
    conn.execute("UPDATE users SET is_active = 1 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    flash('Student activated successfully', 'success')
    return redirect(url_for('admin.students'))

@admin_bp.route('/student/<int:id>/delete', methods=['POST'])
@admin_required
def delete_student(id):
    conn = get_db()
    user_id = conn.execute(
        "SELECT user_id FROM students WHERE id = ?", (id,)
    ).fetchone()['user_id']
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    flash('Student deleted successfully', 'success')
    return redirect(url_for('admin.students'))

@admin_bp.route('/drives')
@admin_required
def drives():
    conn = get_db()
    drives = conn.execute(
        "SELECT pd.*, c.company_name "
        "FROM placement_drives pd "
        "JOIN companies c ON pd.company_id = c.id "
        "ORDER BY pd.created_at DESC"
    ).fetchall()
    conn.close()
    return render_template('admin/drives.html', drives=drives)

@admin_bp.route('/drive/<int:id>/approve', methods=['POST'])
@admin_required
def approve_drive(id):
    conn = get_db()
    conn.execute("UPDATE placement_drives SET status = 'Approved' WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash('Drive approved successfully', 'success')
    return redirect(url_for('admin.drives'))

@admin_bp.route('/drive/<int:id>/reject', methods=['POST'])
@admin_required
def reject_drive(id):
    conn = get_db()
    conn.execute("UPDATE placement_drives SET status = 'Rejected' WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash('Drive rejected successfully', 'success')
    return redirect(url_for('admin.drives'))

@admin_bp.route('/applications')
@admin_required
def applications():
    conn = get_db()
    applications = conn.execute(
        """SELECT a.*, s.full_name AS student_name, s.department,
                  pd.job_title, c.company_name
           FROM applications a
           JOIN students s ON a.student_id = s.id
           JOIN placement_drives pd ON a.drive_id = pd.id
           JOIN companies c ON pd.company_id = c.id
           ORDER BY a.applied_at DESC"""
    ).fetchall()
    conn.close()
    return render_template('admin/applications.html', applications=applications)

@admin_bp.route('/search')
@admin_required
def search():
    query = request.args.get('q', '')
    conn = get_db()

    if query:
        q = f"%{query}%"

        # Search students
        students = conn.execute(
            """SELECT s.*, u.username FROM students s
               JOIN users u ON s.user_id = u.id
               WHERE s.full_name LIKE ? OR s.email LIKE ?
               OR s.phone LIKE ? OR CAST(s.id AS TEXT) LIKE ?""",
            (q, q, q, q)
        ).fetchall()

        # Search companies
        companies = conn.execute(
            """SELECT c.*, u.username FROM companies c
               JOIN users u ON c.user_id = u.id
               WHERE c.company_name LIKE ? OR CAST(c.id AS TEXT) LIKE ?""",
            (q, q)
        ).fetchall()
    else:
        students = []
        companies = []

    conn.close()
    return render_template('admin/search_results.html',
                         students=students,
                         companies=companies,
                         query=query)