import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

# --- App Configuration ---

app = Flask(__name__)

# Secret Key (Required for CSRF, Sessions, and Flask-WTF)
# In production, this should be a long, random, secret string.
app.config['SECRET_KEY'] = 'a-very-secret-key-that-you-should-change'

# Database Configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'student.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- Initialize Extensions ---

# Ensure the instance folder exists
try:
    os.makedirs(app.instance_path)
except OSError:
    pass

# Initialize Database (from models.py)
from models import db, Student, User
db.init_app(app)

# Initialize Bcrypt for password hashing (Task 5)
bcrypt = Bcrypt(app)

# Initialize CSRF Protection (Task 3)
csrf = CSRFProtect(app)

# Initialize Login Manager (Task 3 & 5)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirect to 'login' route if not authenticated
login_manager.login_message_category = 'info' # Flash message category

@login_manager.user_loader
def load_user(user_id):
    """Required callback for Flask-Login to load a user from session."""
    return User.query.get(int(user_id))

# --- Import Forms ---
from forms import StudentForm, RegistrationForm, LoginForm

# --- Database Creation ---
with app.app_context():
    db.create_all()

# --- Authentication Routes (Task 5) ---

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('view_students'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Hash the password (Task 5)
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, password_hash=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', title='Register', form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('view_students'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        # Check password hash (Task 5)
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            flash('Login successful!', 'success')
            # Redirect to the page user was trying to access, or default to view_students
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('view_students'))
        else:
            flash('Login Unsuccessful. Please check username and password.', 'danger')
            
    return render_template('login.html', title='Login', form=form)

@app.route("/logout")
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# --- Main App Routes ---

@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html")

@app.route("/add_student", methods=["POST", "GET"])
@login_required # Protect this route
def add_student():
    # Use WTForms for validation (Task 1) and CSRF (Task 3)
    form = StudentForm()
    if form.validate_on_submit():
        # Data is validated and sanitized
        new_student = Student(
            roll=form.roll.data,
            name=form.name.data,
            dept=form.dept.data
        )
        db.session.add(new_student)
        db.session.commit()
        flash(f'Student {new_student.name} added successfully!', 'success')
        return redirect(url_for('view_students'))
    
    # Handle GET request or form validation failure
    return render_template("addstudent.html", form=form)

@app.route("/view_students", methods=["GET"])
@login_required # Protect this route
def view_students():   
    # Use SQLAlchemy ORM (Task 2: Parameterized Queries)
    students = Student.query.all()
    return render_template("viewstudents.html", students=students)

@app.route('/update_student/<int:roll>', methods=['GET', 'POST'])
@login_required # Protect this route
def update_student(roll):
    # Use SQLAlchemy ORM (Task 2)
    student = Student.query.get_or_404(roll)
    
    # Use WTForms for validation (Task 1) and CSRF (Task 3)
    # Populate the form with existing student data
    form = StudentForm(obj=student)
    
    # Disable roll number field as it's the primary key and shouldn't be changed
    form.roll.render_kw = {'readonly': True} 
    
    if form.validate_on_submit():
        # Update fields
        student.name = form.name.data
        student.dept = form.dept.data
        db.session.commit()
        flash(f'Student {student.name} updated successfully!', 'success')
        return redirect(url_for('view_students'))

    # On GET request, render the template with the pre-filled form
    return render_template('update_student.html', form=form, student=student)


@app.route('/delete_student/<int:roll>', methods=['POST'])
@login_required # Protect this route
def delete_student(roll):
    # Use SQLAlchemy ORM (Task 2)
    student = Student.query.get_or_404(roll)
    db.session.delete(student)
    db.session.commit()
    flash(f'Student {student.name} (Roll: {student.roll}) has been deleted.', 'success')
    return redirect(url_for('view_students'))

# --- Error Handlers (Task 4) ---

@app.errorhandler(404)
def error_404(error):
    """Custom 404 error page to prevent information disclosure."""
    return render_template('404.html'), 404

@app.errorhandler(500)
def error_500(error):
    """Custom 500 error page to prevent information disclosure."""
    # Important: Rollback the session in case a DB error caused the 500
    db.session.rollback()
    return render_template('500.html'), 500

# --- Run Application ---

if __name__ == "__main__":
    app.run(debug=True)