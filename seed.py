import sqlite3
from werkzeug.security import generate_password_hash
from config import DATABASE
import os

def seed():
    # Ensure database exists
    if not os.path.exists(DATABASE):
        from models import init_db
        init_db()

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    # Check if we already seeded
    existing = c.execute("SELECT id FROM users WHERE username='student1'").fetchone()
    if existing:
        print("Database is already seeded!")
        return

    print("Seeding database with mock data...")

    # Define standard password
    hashed_pw = generate_password_hash('password123')

    # Insert Students
    c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ('student1', hashed_pw, 'student'))
    student1_user_id = c.lastrowid
    c.execute("INSERT INTO students (user_id, full_name, email, phone, department, cgpa) VALUES (?, ?, ?, ?, ?, ?)",
              (student1_user_id, 'Alice Smith', 'alice@example.com', '1234567890', 'Computer Science', 8.5))
    student1_id = c.lastrowid

    c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ('student2', hashed_pw, 'student'))
    student2_user_id = c.lastrowid
    c.execute("INSERT INTO students (user_id, full_name, email, phone, department, cgpa) VALUES (?, ?, ?, ?, ?, ?)",
              (student2_user_id, 'Bob Jones', 'bob@example.com', '0987654321', 'Electrical Eng', 7.9))
    student2_id = c.lastrowid

    # Insert Companies
    c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ('techcorp', hashed_pw, 'company'))
    comp1_user_id = c.lastrowid
    c.execute("INSERT INTO companies (user_id, company_name, hr_contact, website, description, approval_status) VALUES (?, ?, ?, ?, ?, ?)",
              (comp1_user_id, 'TechCorp', 'hr@techcorp.com', 'www.techcorp.com', 'Leading tech firm.', 'Approved'))
    comp1_id = c.lastrowid

    c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ('innovateio', hashed_pw, 'company'))
    comp2_user_id = c.lastrowid
    c.execute("INSERT INTO companies (user_id, company_name, hr_contact, website, description, approval_status) VALUES (?, ?, ?, ?, ?, ?)",
              (comp2_user_id, 'Innovate.io', 'jobs@innovate.io', 'www.innovate.io', 'A hyper-growth startup.', 'Approved'))
    comp2_id = c.lastrowid

    # Insert Placement Drives
    c.execute("INSERT INTO placement_drives (company_id, job_title, job_description, eligibility_criteria, application_deadline, salary, location, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
              (comp1_id, 'Software Engineer', 'Develop awesome software.', 'B.Tech CS, CGPA > 8.0', '2026-12-31', '12 LPA', 'Bangalore', 'Approved'))
    drive1_id = c.lastrowid

    c.execute("INSERT INTO placement_drives (company_id, job_title, job_description, eligibility_criteria, application_deadline, salary, location, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
              (comp2_id, 'Data Analyst', 'Analyze the data.', 'Any degree, CGPA > 7.0', '2026-12-31', '8 LPA', 'Remote', 'Approved'))
    drive2_id = c.lastrowid
    
    # Insert unapproved drive
    c.execute("INSERT INTO placement_drives (company_id, job_title, job_description, eligibility_criteria, application_deadline, salary, location, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
              (comp1_id, 'Frontend Dev', 'Build React UIs.', 'HTML, CSS, JS', '2026-12-31', '10 LPA', 'Pune', 'Pending'))
    
    # Insert Applications
    c.execute("INSERT INTO applications (student_id, drive_id, status) VALUES (?, ?, ?)",
              (student1_id, drive1_id, 'Applied'))
    c.execute("INSERT INTO applications (student_id, drive_id, status) VALUES (?, ?, ?)",
              (student2_id, drive2_id, 'Shortlisted'))
    
    conn.commit()
    conn.close()
    print("Database seeded with sample data successfully!")

if __name__ == '__main__':
    seed()
