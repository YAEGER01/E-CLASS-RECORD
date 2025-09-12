import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.utils import secure_filename
from models import User, Student, Instructor, Class, StudentClass, generate_class_codes
from db_conn import init_database_with_app, db_conn
from models import db
from functools import wraps

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour
logger.info("Flask application initialized with session configuration")


@app.route("/")
def home():
    logger.info("Home page accessed")
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        school_id = request.form.get('schoolId', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', 'student')

        logger.info(f"Login attempt for school ID: {school_id}, role: {role}")

        # Validate input
        if not school_id or not password:
            flash("Please enter both school ID and password.", "error")
            logger.warning("Login failed: Missing credentials")
            return render_template("login.html", role=role)

        # Find user
        user = User.query.filter_by(school_id=school_id).first()

        if not user:
            flash("Invalid school ID or password.", "error")
            logger.warning(f"Login failed: User {school_id} not found")
            return render_template("login.html", role=role)

        # Check password
        if not user.check_password(password):
            flash("Invalid school ID or password.", "error")
            logger.warning(f"Login failed: Invalid password for user {school_id}")
            return render_template("login.html", role=role)

        # Check role
        if user.role != role:
            flash("Invalid role for this account.", "error")
            logger.warning(f"Login failed: Role mismatch for user {school_id}")
            return render_template("login.html", role=role)

        # Login successful
        session['user_id'] = user.id
        session['school_id'] = user.school_id
        session['role'] = user.role
        session.permanent = True

        logger.info(f"User {school_id} logged in successfully")

        # Redirect based on role
        if user.role == 'admin':
            flash(f"Welcome back, Admin {user.school_id}!", "success")
            return redirect(url_for('admin_dashboard'))
        elif user.role == 'instructor':
            flash(f"Welcome back, Instructor {user.school_id}!", "success")
            return redirect(url_for('instructor_dashboard'))
        else:  # student
            flash(f"Welcome back, {user.school_id}!", "success")
            return redirect(url_for('student_dashboard'))

    # GET
    role = request.args.get('role', 'student')
    logger.info(f"Login page accessed with role: {role}")
    return render_template("login.html", role=role)

@app.route('/index')
def index():
    logger.info("Index page accessed")
    return render_template('index.html')

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    # Check for URL parameters for direct login
    url_username = request.args.get('username', '').strip()
    url_password = request.args.get('password', '')
    url_role = request.args.get('role', 'admin')

    # If URL parameters are provided, try to authenticate directly
    if url_username and url_password:
        logger.info(f"Direct admin login attempt for school ID: {url_username}")

        # Find user
        user = User.query.filter_by(school_id=url_username).first()

        if user and user.check_password(url_password) and user.role == url_role:
            # Login successful
            session['user_id'] = user.id
            session['school_id'] = user.school_id
            session['role'] = user.role
            session.permanent = True

            logger.info(f"Direct admin login successful for {url_username}")
            return redirect(url_for('admin_dashboard'))
        else:
            logger.warning(f"Direct admin login failed for {url_username}")
            return render_template('adminlogin.html', error="Invalid credentials.")

    if request.method == 'POST':
        school_id = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        role = 'admin'

        logger.info(f"Admin login attempt for school ID: {school_id}")

        # Validate input
        if not school_id or not password:
            logger.warning("Admin login failed: Missing credentials")
            return render_template('adminlogin.html', error="Please enter both school ID and password.")

        # Find user
        user = User.query.filter_by(school_id=school_id).first()

        if not user:
            logger.warning(f"Admin login failed: User {school_id} not found")
            return render_template('adminlogin.html', error="Invalid admin credentials.")

        # Check password
        if not user.check_password(password):
            logger.warning(f"Admin login failed: Invalid password for user {school_id}")
            return render_template('adminlogin.html', error="Invalid admin credentials.")

        # Check role
        if user.role != role:
            logger.warning(f"Admin login failed: Role mismatch for user {school_id}")
            return render_template('adminlogin.html', error="Invalid admin credentials.")

        # Login successful
        session['user_id'] = user.id
        session['school_id'] = user.school_id
        session['role'] = user.role
        session.permanent = True

        logger.info(f"Admin {school_id} logged in successfully")
        return redirect(url_for('admin_dashboard'))

    logger.info("Admin login page accessed")
    return render_template('adminlogin.html')


@app.route('/instructor-login', methods=['GET', 'POST'])
def instructor_login():
    # Check for URL parameters for direct login
    url_username = request.args.get('username', '').strip()
    url_password = request.args.get('password', '')
    url_role = request.args.get('role', 'instructor')

    # If URL parameters are provided, try to authenticate directly
    if url_username and url_password:
        logger.info(f"Direct instructor login attempt for school ID: {url_username}")

        # Find user
        user = User.query.filter_by(school_id=url_username).first()

        if user and user.check_password(url_password) and user.role == url_role:
            # Login successful
            session['user_id'] = user.id
            session['school_id'] = user.school_id
            session['role'] = user.role
            session.permanent = True

            logger.info(f"Direct instructor login successful for {url_username}")
            return redirect(url_for('instructor_dashboard'))
        else:
            logger.warning(f"Direct instructor login failed for {url_username}")
            return render_template('instructorlogin.html', error="Invalid credentials.")

    if request.method == 'POST':
        school_id = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        role = 'instructor'

        logger.info(f"Instructor login attempt for school ID: {school_id}")

        # Validate input
        if not school_id or not password:
            logger.warning("Instructor login failed: Missing credentials")
            return render_template('instructorlogin.html', error="Please enter both school ID and password.")

        # Find user
        user = User.query.filter_by(school_id=school_id).first()

        if not user:
            logger.warning(f"Instructor login failed: User {school_id} not found")
            return render_template('instructorlogin.html', error="Invalid instructor credentials.")

        # Check password
        if not user.check_password(password):
            logger.warning(f"Instructor login failed: Invalid password for user {school_id}")
            return render_template('instructorlogin.html', error="Invalid instructor credentials.")

        # Check role
        if user.role != role:
            logger.warning(f"Instructor login failed: Role mismatch for user {school_id}")
            return render_template('instructorlogin.html', error="Invalid instructor credentials.")

        # Login successful
        session['user_id'] = user.id
        session['school_id'] = user.school_id
        session['role'] = user.role
        session.permanent = True

        logger.info(f"Instructor {school_id} logged in successfully")
        return redirect(url_for('instructor_dashboard'))

    logger.info("Instructor login page accessed")
    return render_template('instructorlogin.html')

# Instructor Class Management Routes
@app.route('/instructor/classes')
@login_required
def instructor_classes():
    """Display instructor's class management page."""
    if session.get('role') != 'instructor':
        flash("Access denied. Instructor privileges required.", "error")
        return redirect(url_for('home'))

    user = db.session.get(User, session['user_id'])
    if not user:
        # Session contains invalid user ID (likely due to database reset)
        session.clear()
        flash("Session expired. Please log in again.", "error")
        return redirect(url_for('login'))

    instructor = Instructor.query.filter_by(user_id=user.id).first()

    if not instructor:
        flash("Instructor profile not found.", "error")
        return redirect(url_for('home'))

    logger.info(f"Instructor {user.school_id} accessed class management")
    return render_template('instructor_classes.html')

@app.route('/api/instructor/classes', methods=['GET'])
@login_required
def get_instructor_classes():
    """Get all classes for the logged-in instructor."""
    if session.get('role') != 'instructor':
        return jsonify({'error': 'Access denied'}), 403

    user = db.session.get(User, session['user_id'])
    instructor = Instructor.query.filter_by(user_id=user.id).first()

    if not instructor:
        return jsonify({'error': 'Instructor profile not found'}), 404

    classes = Class.query.filter_by(instructor_id=instructor.id).all()
    classes_data = []

    for cls in classes:
        classes_data.append({
            'id': cls.id,
            'year': cls.year,
            'semester': cls.semester,
            'course': cls.course,
            'track': cls.track,
            'section': cls.section,
            'schedule': cls.schedule,
            'class_id': cls.class_id,
            'class_code': cls.class_code,
            'join_code': cls.join_code,
            'created_at': cls.created_at.isoformat() if cls.created_at else None,
            'updated_at': cls.updated_at.isoformat() if cls.updated_at else None
        })

    logger.info(f"Retrieved {len(classes_data)} classes for instructor {user.school_id}")
    return jsonify({'classes': classes_data})

@app.route('/api/instructor/classes', methods=['POST'])
@login_required
def create_class():
    """Create a new class for the logged-in instructor."""
    if session.get('role') != 'instructor':
        return jsonify({'error': 'Access denied'}), 403

    user = User.query.get(session['user_id'])
    instructor = Instructor.query.filter_by(user_id=user.id).first()

    if not instructor:
        return jsonify({'error': 'Instructor profile not found'}), 404

    data = request.get_json()

    # Validate required fields
    required_fields = ['year', 'semester', 'course', 'track', 'section', 'schedule']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400

    # Validate section format (should be like "1A", "2B", etc.)
    section = data['section']
    if not (len(section) == 2 and section[0].isdigit() and section[1].isalpha()):
        return jsonify({'error': 'Section must be in format like "1A", "2B", etc.'}), 400

    try:
        # Generate unique class codes
        class_code, join_code = generate_class_codes()

        # Ensure join_code is unique (very unlikely to collide, but just in case)
        while Class.query.filter_by(join_code=join_code).first():
            class_code, join_code = generate_class_codes()

        new_class = Class(
            instructor_id=instructor.id,
            year=data['year'],
            semester=data['semester'],
            course=data['course'],
            track=data['track'],
            section=section,
            schedule=data['schedule'],
            class_code=class_code,
            join_code=join_code
        )

        db.session.add(new_class)
        db.session.commit()

        logger.info(f"Instructor {user.school_id} created class: {new_class.class_id}")
        return jsonify({
            'success': True,
            'message': 'Class created successfully',
            'class': {
                'id': new_class.id,
                'year': new_class.year,
                'semester': new_class.semester,
                'course': new_class.course,
                'track': new_class.track,
                'section': new_class.section,
                'schedule': new_class.schedule,
                'class_id': new_class.class_id,
                'class_code': new_class.class_code,
                'join_code': new_class.join_code
            }
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to create class for instructor {user.school_id}: {str(e)}")
        return jsonify({'error': 'Failed to create class'}), 500

@app.route('/api/instructor/classes/<int:class_id>', methods=['PUT'])
@login_required
def update_class(class_id):
    """Update an existing class."""
    if session.get('role') != 'instructor':
        return jsonify({'error': 'Access denied'}), 403

    user = db.session.get(User, session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 401

    instructor = Instructor.query.filter_by(user_id=user.id).first()

    if not instructor:
        return jsonify({'error': 'Instructor profile not found'}), 404

    # Find the class and verify ownership
    class_obj = Class.query.filter_by(id=class_id, instructor_id=instructor.id).first()
    if not class_obj:
        return jsonify({'error': 'Class not found or access denied'}), 404

    data = request.get_json()

    # Validate required fields
    required_fields = ['year', 'semester', 'course', 'track', 'section', 'schedule']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400

    # Validate section format
    section = data['section']
    if not (len(section) == 2 and section[0].isdigit() and section[1].isalpha()):
        return jsonify({'error': 'Section must be in format like "1A", "2B", etc.'}), 400

    try:
        class_obj.year = data['year']
        class_obj.semester = data['semester']
        class_obj.course = data['course']
        class_obj.track = data['track']
        class_obj.section = section
        class_obj.schedule = data['schedule']

        db.session.commit()

        logger.info(f"Instructor {user.school_id} updated class {class_id}: {class_obj.class_id}")
        return jsonify({
            'success': True,
            'message': 'Class updated successfully',
            'class': {
                'id': class_obj.id,
                'year': class_obj.year,
                'semester': class_obj.semester,
                'course': class_obj.course,
                'track': class_obj.track,
                'section': class_obj.section,
                'schedule': class_obj.schedule,
                'class_id': class_obj.class_id,
                'class_code': class_obj.class_code,
                'join_code': class_obj.join_code
            }
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to update class {class_id} for instructor {user.school_id}: {str(e)}")
        return jsonify({'error': 'Failed to update class'}), 500

@app.route('/api/instructor/classes/<int:class_id>', methods=['DELETE'])
@login_required
def delete_class(class_id):
    """Delete a class."""
    if session.get('role') != 'instructor':
        return jsonify({'error': 'Access denied'}), 403

    user = db.session.get(User, session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 401

    instructor = Instructor.query.filter_by(user_id=user.id).first()

    if not instructor:
        return jsonify({'error': 'Instructor profile not found'}), 404

    # Find the class and verify ownership
    class_obj = Class.query.filter_by(id=class_id, instructor_id=instructor.id).first()
    if not class_obj:
        return jsonify({'error': 'Class not found or access denied'}), 404

    try:
        class_id_display = class_obj.class_id
        db.session.delete(class_obj)
        db.session.commit()

        logger.info(f"Instructor {user.school_id} deleted class: {class_id_display}")
        return jsonify({
            'success': True,
            'message': 'Class deleted successfully'
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to delete class {class_id} for instructor {user.school_id}: {str(e)}")
        return jsonify({'error': 'Failed to delete class'}), 500


# Student Class Management Routes
@app.route('/api/student/join-class', methods=['POST'])
@login_required
def join_class():
    """Join a class using join code."""
    if session.get('role') != 'student':
        return jsonify({'error': 'Access denied. Student privileges required.'}), 403

    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 401

    student = Student.query.filter_by(user_id=user.id).first()
    if not student:
        return jsonify({'error': 'Student profile not found'}), 404

    data = request.get_json()
    join_code = data.get('join_code', '').strip().upper()

    if not join_code:
        return jsonify({'error': 'Join code is required'}), 400

    # Find class by join code
    class_obj = Class.query.filter_by(join_code=join_code).first()
    if not class_obj:
        return jsonify({'error': 'Invalid join code. Class not found.'}), 404

    # Check if student is already enrolled
    existing_enrollment = StudentClass.query.filter_by(
        student_id=student.id,
        class_id=class_obj.id
    ).first()

    if existing_enrollment:
        return jsonify({'error': 'You are already enrolled in this class'}), 400

    try:
        # Create enrollment
        enrollment = StudentClass(
            student_id=student.id,
            class_id=class_obj.id
        )
        db.session.add(enrollment)
        db.session.commit()

        logger.info(f"Student {user.school_id} joined class: {class_obj.class_id}")
        return jsonify({
            'success': True,
            'message': f'Successfully joined class: {class_obj.class_id}',
            'class': {
                'id': class_obj.id,
                'class_id': class_obj.class_id,
                'course': class_obj.course,
                'section': class_obj.section,
                'schedule': class_obj.schedule
            }
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to join class for student {user.school_id}: {str(e)}")
        return jsonify({'error': 'Failed to join class'}), 500


@app.route('/api/student/joined-classes', methods=['GET'])
@login_required
def get_joined_classes():
    """Get all classes joined by the logged-in student."""
    if session.get('role') != 'student':
        return jsonify({'error': 'Access denied. Student privileges required.'}), 403

    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 401

    student = Student.query.filter_by(user_id=user.id).first()
    if not student:
        return jsonify({'error': 'Student profile not found'}), 404

    # Get all enrollments for this student with joined instructor and user data
    enrollments = StudentClass.query.filter_by(student_id=student.id).all()
    classes_data = []

    for enrollment in enrollments:
        class_obj = enrollment.class_obj
        instructor_name = 'Unknown'
        if class_obj.instructor:
            # Get the instructor's user information
            instructor_user = User.query.get(class_obj.instructor.user_id)
            if instructor_user:
                instructor_name = instructor_user.school_id

        classes_data.append({
            'id': class_obj.id,
            'class_id': class_obj.class_id,
            'year': class_obj.year,
            'semester': class_obj.semester,
            'course': class_obj.course,
            'track': class_obj.track,
            'section': class_obj.section,
            'schedule': class_obj.schedule,
            'class_code': class_obj.class_code,
            'join_code': class_obj.join_code,
            'instructor_name': instructor_name,
            'joined_at': enrollment.joined_at.isoformat() if enrollment.joined_at else None
        })

    logger.info(f"Retrieved {len(classes_data)} joined classes for student {user.school_id}")
    return jsonify({'classes': classes_data})


@app.route('/student-login', methods=['GET', 'POST'])
def student_login():
    # Check for URL parameters for direct login
    url_username = request.args.get('username', '').strip()
    url_password = request.args.get('password', '')
    url_role = request.args.get('role', 'student')

    # If URL parameters are provided, try to authenticate directly
    if url_username and url_password:
        logger.info(f"Direct login attempt for school ID: {url_username}")

        # Find user
        user = User.query.filter_by(school_id=url_username).first()

        if user and user.check_password(url_password) and user.role == url_role:
            # Login successful
            session['user_id'] = user.id
            session['school_id'] = user.school_id
            session['role'] = user.role
            session.permanent = True

            logger.info(f"Direct login successful for {url_username}")
            return redirect(url_for('student_dashboard'))
        else:
            logger.warning(f"Direct login failed for {url_username}")
            return render_template('studentlogin.html', error="Invalid credentials.")

    if request.method == 'POST':
        school_id = request.form.get('username', '').strip()  # Form uses 'username' field
        password = request.form.get('password', '')
        role = 'student'  # This is the student login page

        logger.info(f"Student login attempt for school ID: {school_id}")

        # Validate input
        if not school_id or not password:
            logger.warning("Student login failed: Missing credentials")
            return render_template('studentlogin.html', error="Please enter both school ID and password.")

        # Find user
        user = User.query.filter_by(school_id=school_id).first()

        if not user:
            logger.warning(f"Student login failed: User {school_id} not found")
            return render_template('studentlogin.html', error="Invalid student credentials.")

        # Check password
        if not user.check_password(password):
            logger.warning(f"Student login failed: Invalid password for user {school_id}")
            return render_template('studentlogin.html', error="Invalid student credentials.")

        # Check role
        if user.role != role:
            logger.warning(f"Student login failed: Role mismatch for user {school_id}")
            return render_template('studentlogin.html', error="Invalid student credentials.")

        # Login successful
        session['user_id'] = user.id
        session['school_id'] = user.school_id
        session['role'] = user.role
        session.permanent = True

        logger.info(f"Student {school_id} logged in successfully")
        return redirect(url_for('student_dashboard'))

    logger.info("Student login page accessed")
    return render_template('studentlogin.html')

@app.route('/about')
def about():
    logger.info("About page accessed")
    return render_template('about.html')

@app.route('/logout')
def logout():
    user_id = session.get('user_id')
    school_id = session.get('school_id')
    session.clear()
    logger.info(f"User {school_id} (ID: {user_id}) logged out")
    flash("You have been logged out successfully.", "info")
    return redirect(url_for('home'))

@app.route('/student-dashboard')
def student_dashboard():
    if 'user_id' not in session:
        flash("Please log in to access this page.", "warning")
        return redirect(url_for('login'))

    user = db.session.get(User, session['user_id'])
    if not user or user.role != 'student':
        session.clear()
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))

    logger.info(f"Student dashboard accessed by {user.school_id}")
    return render_template('student_dashboard.html', user=user)

@app.route('/instructor-dashboard')
def instructor_dashboard():
    if 'user_id' not in session:
        flash("Please log in to access this page.", "warning")
        return redirect(url_for('login'))

    user = db.session.get(User, session['user_id'])
    if not user or user.role != 'instructor':
        session.clear()
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))

    logger.info(f"Instructor dashboard accessed by {user.school_id}")
    return render_template('instructor_dashboard.html', user=user)

@app.route('/admin-dashboard')
def admin_dashboard():
    if 'user_id' not in session:
        flash("Please log in to access this page.", "warning")
        return redirect(url_for('login'))

    user = db.session.get(User, session['user_id'])
    if not user or user.role != 'admin':
        session.clear()
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))

    logger.info(f"Admin dashboard accessed by {user.school_id}")
    return render_template('admin_dashboard.html', user=user)

@app.route('/admin/create-instructor', methods=['POST'])
def create_instructor():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    user = db.session.get(User, session['user_id'])
    if not user or user.role != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    try:
        data = request.get_json()

        school_id = data.get('schoolId', '').strip()
        password = data.get('password', '')
        department = data.get('department', '').strip()
        specialization = data.get('specialization', '').strip()
        employee_id = data.get('employeeId', '').strip()

        # Validation
        errors = []

        # Check if school ID already exists
        existing_user = User.query.filter_by(school_id=school_id).first()
        if existing_user:
            errors.append("School ID already exists")

        # Validate required fields
        if not school_id:
            errors.append("School ID is required")
        if not password:
            errors.append("Password is required")
        if not department:
            errors.append("Department is required")

        # Password strength validation - more reasonable requirements
        if len(password) < 6:
            errors.append("Password must be at least 6 characters long")
        if not (any(c.isupper() for c in password) or any(c.islower() for c in password)):
            errors.append("Password must contain at least one letter (upper or lowercase)")
        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number")

        if errors:
            logger.warning(f"Instructor creation failed: {errors}")
            return jsonify({'success': False, 'message': '; '.join(errors)}), 400

        # Create instructor user
        new_instructor = User(school_id=school_id, role='instructor')
        new_instructor.set_password(password)

        # Create instructor profile
        instructor_profile = Instructor(
            department=department,
            specialization=specialization if specialization else None,
            employee_id=employee_id if employee_id else None
        )

        # Save to database
        db.session.add(new_instructor)
        db.session.flush()  # Get user ID
        instructor_profile.user_id = new_instructor.id
        db.session.add(instructor_profile)
        db.session.commit()

        logger.info(f"Instructor created successfully: {school_id} by admin {user.school_id}")
        return jsonify({
            'success': True,
            'message': f'Instructor {school_id} created successfully!',
            'instructor': {
                'school_id': school_id,
                'department': department,
                'specialization': specialization,
                'employee_id': employee_id
            }
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"Instructor creation failed: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to create instructor account'}), 500

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        logger.info("Registration form submitted")

        # Get form data
        school_id = request.form.get('schoolId', '').strip()
        course = request.form.get('course', '').strip()
        track = request.form.get('track', '').strip() or None
        year_level = request.form.get('yearLevel', '').strip()
        section = request.form.get('section', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirmPassword', '')

        # Validation
        errors = []

        # Check if school ID already exists
        existing_user = User.query.filter_by(school_id=school_id).first()
        if existing_user:
            errors.append("School ID already registered")
            logger.warning(f"Registration failed: School ID {school_id} already exists")

        # Validate required fields
        if not school_id:
            errors.append("School ID is required")
        if not course:
            errors.append("Course is required")
        if not year_level:
            errors.append("Year level is required")
        if not section:
            errors.append("Section is required")
        if not password:
            errors.append("Password is required")
        if password != confirm_password:
            errors.append("Passwords do not match")

        # Password strength validation
        if len(password) < 6:
            errors.append("Password must be at least 6 characters long")
        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number")

        if errors:
            for error in errors:
                flash(error, 'error')
            logger.warning(f"Registration validation failed for school ID {school_id}: {errors}")
            # Repopulate form with previously entered data
            return render_template('register.html',
                                 form_data={
                                     'schoolId': school_id,
                                     'course': course,
                                     'track': track,
                                     'yearLevel': year_level,
                                     'section': section
                                 })

        try:
            # Create user
            new_user = User(school_id=school_id, role='student')
            new_user.set_password(password)

            # Handle file uploads
            upload_dir = os.path.join(app.root_path, 'static', 'uploads')
            os.makedirs(upload_dir, exist_ok=True)

            id_front_path = None
            id_back_path = None
            face_photo_path = None

            if 'idFront' in request.files:
                id_front_file = request.files['idFront']
                if id_front_file and id_front_file.filename:
                    filename = secure_filename(f"{school_id}_id_front_{id_front_file.filename}")
                    id_front_file.save(os.path.join(upload_dir, filename))
                    id_front_path = f"uploads/{filename}"

            if 'idBack' in request.files:
                id_back_file = request.files['idBack']
                if id_back_file and id_back_file.filename:
                    filename = secure_filename(f"{school_id}_id_back_{id_back_file.filename}")
                    id_back_file.save(os.path.join(upload_dir, filename))
                    id_back_path = f"uploads/{filename}"

            if 'facePhoto' in request.files:
                face_photo_file = request.files['facePhoto']
                if face_photo_file and face_photo_file.filename:
                    filename = secure_filename(f"{school_id}_face_{face_photo_file.filename}")
                    face_photo_file.save(os.path.join(upload_dir, filename))
                    face_photo_path = f"uploads/{filename}"

            # Create student profile
            student_profile = Student(
                course=course,
                track=track,
                year_level=int(year_level),
                section=section,
                id_front_path=id_front_path,
                id_back_path=id_back_path,
                face_photo_path=face_photo_path
            )

            # Save to database
            db.session.add(new_user)
            db.session.flush()  # Get user ID
            student_profile.user_id = new_user.id
            db.session.add(student_profile)
            db.session.commit()

            logger.info(f"User registered successfully: {school_id}")
            flash("Registration successful! Please log in.", 'success')
            return redirect(url_for('login'))

        except Exception as e:
            db.session.rollback()
            logger.error(f"Registration failed for {school_id}: {str(e)}")
            flash("Registration failed. Please try again.", 'error')
            return render_template('register.html',
                                 form_data={
                                     'schoolId': school_id,
                                     'course': course,
                                     'track': track,
                                     'yearLevel': year_level,
                                     'section': section
                                 })

    logger.info("Registration page accessed")
    return render_template('register.html')



# Initialize database on app startup
if __name__ == "__main__":
    logger.info("Application startup initiated")
    if init_database_with_app(app):
        logger.info("🚀 Starting Flask application...")
        app.run(debug=True)
    else:
        logger.error("❌ Failed to initialize database. Please check your database configuration.")
        exit(1)
