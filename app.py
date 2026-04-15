import os
from flask import Flask, redirect, url_for
from flask_login import LoginManager
from config import SECRET_KEY, UPLOAD_FOLDER
from helpers import get_db, load_user
import models

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Flask-Login setup
login_manager = LoginManager(app)
login_manager.login_view    = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.user_loader(load_user)

# Register Blueprints
from auth    import auth_bp
from admin   import admin_bp
from company import company_bp
from student import student_bp

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp,   url_prefix='/admin')
app.register_blueprint(company_bp, url_prefix='/company')
app.register_blueprint(student_bp, url_prefix='/student')

@app.route('/')
def index():
    return redirect(url_for('auth.login'))

if __name__ == '__main__':
    models.init_db()
    app.run(debug=True)