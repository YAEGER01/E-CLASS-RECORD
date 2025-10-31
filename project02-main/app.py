import logging
import uuid
import hashlib
import random
import json
from datetime import datetime
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    jsonify,
)
from flask_socketio import SocketIO, emit, join_room, leave_room

# Create Flask app
app = Flask(__name__)

# Add enumerate to Jinja environment
app.jinja_env.globals.update(enumerate=enumerate)
from flask_wtf.csrf import CSRFProtect, generate_csrf
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from db_conn import get_db_connection

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Helper function to generate class codes
def generate_class_codes():
    """Generate unique 36-character class code and 6-digit join code"""
    class_code = str(uuid.uuid4())
    hash_obj = hashlib.md5(class_code.encode())
    hash_hex = hash_obj.hexdigest()
    join_code = "".join(c for c in hash_hex[:6] if c.isdigit())
    while len(join_code) < 6:
        join_code += str(random.randint(0, 9))
    return class_code, join_code[:6]


# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


app = Flask(__name__)
app.secret_key = "dev-secret-key-change-in-production"

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")


@app.route("/")
def home():
    logger.info("Home page accessed")
    return render_template("index.html")


@app.route("/index")
def index():
    logger.info("Index page accessed")
    return render_template("index.html")


@app.route("/welcome", methods=["GET"])
def welcome():
    logger.info(f"Request received: {request.method} {request.path}")
    return jsonify({"message": "Welcome to the Flask API Service!"})


@app.route("/login")
def login():
    """Display the role selection page (landing page with login options)"""
    logger.info("Login role selection page accessed")
    return render_template("login.html")


@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    # Initialize admin login attempt tracking if not exists
    if "admin_failed_attempts" not in session:
        session["admin_failed_attempts"] = 0
    if "admin_timeout_until" not in session:
        session["admin_timeout_until"] = None
    if "admin_timeout_duration" not in session:
        session["admin_timeout_duration"] = 0

    # Check if currently in timeout period
    current_time = datetime.now()
    timeout_until_str = session.get("admin_timeout_until")

    if (
        timeout_until_str
        and timeout_until_str != "None"
        and isinstance(timeout_until_str, str)
    ):
        try:
            timeout_until = datetime.strptime(timeout_until_str, "%Y-%m-%d %H:%M:%S")
        except (ValueError, AttributeError):
            timeout_until = None

        if timeout_until and current_time < timeout_until:
            remaining_seconds = int((timeout_until - current_time).total_seconds())
            flash(
                f"Too many failed login attempts. Please wait {remaining_seconds} seconds before trying again.",
                "error",
            )

    if request.method == "POST":
        school_id = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = "admin"

        logger.info(f"Admin login attempt for school ID: {school_id}")

        if not school_id or not password:
            logger.warning("Admin login failed: Missing credentials")
            flash("Please enter both school ID and password.", "error")
            return redirect(url_for("admin_login"))

        # Find user using raw SQL
        try:
            with get_db_connection().cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE school_id = %s", (school_id,))
                user = cursor.fetchone()
        except Exception as e:
            logger.error(f"Database error during admin user lookup: {str(e)}")
            flash("An error occurred. Please try again.", "error")
            return redirect(url_for("admin_login"))

        if not user:
            logger.warning(f"Admin login failed: User {school_id} not found")
            session["admin_failed_attempts"] += 1
            flash("Invalid admin credentials.", "error")
            return redirect(url_for("admin_login"))

        # Check password
        if not check_password_hash(user["password_hash"], password):
            logger.warning(f"Admin login failed: Invalid password for user {school_id}")
            session["admin_failed_attempts"] += 1
            flash("Invalid admin credentials.", "error")
            return redirect(url_for("admin_login"))

        # Check role
        if user["role"] != role:
            logger.warning(f"Admin login failed: Role mismatch for user {school_id}")
            session["admin_failed_attempts"] += 1
            flash("Invalid admin credentials.", "error")
            return redirect(url_for("admin_login"))

        # Login successful - reset timeout counters
        session["admin_failed_attempts"] = 0
        session["admin_timeout_until"] = None
        session["admin_timeout_duration"] = 0

        session["user_id"] = user["id"]
        session["school_id"] = user["school_id"]
        session["role"] = user["role"]
        session.permanent = True

        logger.info(f"Admin {school_id} logged in successfully")
        return redirect(url_for("admin_dashboard"))

    logger.info("Admin login page accessed")
    return render_template("adminlogin.html")


@app.route("/instructor-login", methods=["GET", "POST"])
def instructor_login():
    if request.method == "POST":
        school_id = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = "instructor"

        logger.info(f"Instructor login attempt for school ID: {school_id}")

        if not school_id or not password:
            logger.warning("Instructor login failed: Missing credentials")
            flash("Please enter both school ID and password.", "error")
            return redirect(url_for("instructor_login"))

        # Find user using raw SQL
        try:
            with get_db_connection().cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE school_id = %s", (school_id,))
                user = cursor.fetchone()
        except Exception as e:
            logger.error(f"Database error during instructor user lookup: {str(e)}")
            flash("An error occurred. Please try again.", "error")
            return redirect(url_for("instructor_login"))

        if not user:
            logger.warning(f"Instructor login failed: User {school_id} not found")
            flash("Invalid instructor credentials.", "error")
            return redirect(url_for("instructor_login"))

        # Check password
        if not check_password_hash(user["password_hash"], password):
            logger.warning(
                f"Instructor login failed: Invalid password for user {school_id}"
            )
            flash("Invalid instructor credentials.", "error")
            return redirect(url_for("instructor_login"))

        # Check role
        if user["role"] != role:
            logger.warning(
                f"Instructor login failed: Role mismatch for user {school_id}"
            )
            flash("Invalid instructor credentials.", "error")
            return redirect(url_for("instructor_login"))

        # Check if instructor is suspended
        try:
            with get_db_connection().cursor() as cursor:
                cursor.execute(
                    "SELECT status FROM instructors WHERE user_id = %s", (user["id"],)
                )
                instructor = cursor.fetchone()
        except Exception as e:
            logger.error(f"Database error during instructor status check: {str(e)}")
            flash("An error occurred. Please try again.", "error")
            return redirect(url_for("instructor_login"))

        if instructor and instructor["status"] == "suspended":
            logger.warning(
                f"Instructor login failed: Account suspended for user {school_id}"
            )
            flash(
                "Your instructor account has been suspended. Please contact an administrator.",
                "error",
            )
            return redirect(url_for("instructor_login"))

        # Login successful
        # Login successful
        session["user_id"] = user["id"]
        session["school_id"] = user["school_id"]
        session["role"] = user["role"]
        session.permanent = True

        # Fetch and store instructor_id for this user
        with get_db_connection().cursor() as cursor:
            cursor.execute(
                "SELECT id FROM instructors WHERE user_id = %s", (user["id"],)
            )
            instr = cursor.fetchone()
            if instr:
                session["instructor_id"] = instr["id"]

        logger.info(f"Instructor {school_id} logged in successfully")
        return redirect(url_for("instructor_dashboard"))

    logger.info("Instructor login page accessed")
    return render_template("instructorlogin.html")


@app.route("/student-login", methods=["GET", "POST"])
def student_login():
    if request.method == "POST":
        school_id = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = "student"

        logger.info(f"Student login attempt for school ID: {school_id}")

        if not school_id or not password:
            logger.warning("Student login failed: Missing credentials")
            flash("Please enter both school ID and password.", "error")
            return redirect(url_for("student_login"))

        # Find user using raw SQL
        try:
            with get_db_connection().cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE school_id = %s", (school_id,))
                user = cursor.fetchone()
        except Exception as e:
            logger.error(f"Database error during student user lookup: {str(e)}")
            flash("An error occurred. Please try again.", "error")
            return redirect(url_for("student_login"))

        if not user:
            logger.warning(f"Student login failed: User {school_id} not found")
            flash("Invalid student credentials.", "error")
            return redirect(url_for("student_login"))

        # Check password
        if not check_password_hash(user["password_hash"], password):
            logger.warning(
                f"Student login failed: Invalid password for user {school_id}"
            )
            flash("Invalid student credentials.", "error")
            return redirect(url_for("student_login"))

        # Check role
        if user["role"] != role:
            logger.warning(f"Student login failed: Role mismatch for user {school_id}")
            flash("Invalid student credentials.", "error")
            return redirect(url_for("student_login"))

        # Login successful
        session["user_id"] = user["id"]
        session["school_id"] = user["school_id"]
        session["role"] = user["role"]
        session.permanent = True

        logger.info(f"Student {school_id} logged in successfully")
        return redirect(url_for("student_dashboard"))

    logger.info("Student login page accessed")
    return render_template("studentlogin.html")


@app.route("/logout")
def logout():
    user_id = session.get("user_id")
    school_id = session.get("school_id")
    session.clear()
    logger.info(f"User {school_id} (ID: {user_id}) logged out")
    return redirect(url_for("home"))


@app.route("/student-dashboard")
@login_required
def student_dashboard():
    if session.get("role") != "student":
        session.clear()
        flash("Unauthorized access.", "error")
        return redirect(url_for("login"))

    # Get complete user and student data from database
    try:
        with get_db_connection().cursor() as cursor:
            # Get user data
            cursor.execute("SELECT * FROM users WHERE id = %s", (session["user_id"],))
            user_data = cursor.fetchone()

            if not user_data:
                session.clear()
                flash("Session expired. Please log in again.", "error")
                return redirect(url_for("login"))

            # Get student profile data
            cursor.execute(
                """SELECT s.*, pi.first_name, pi.last_name, pi.middle_name, pi.email
                FROM students s
                LEFT JOIN personal_info pi ON s.personal_info_id = pi.id
                WHERE s.user_id = %s""",
                (session["user_id"],),
            )
            student_data = cursor.fetchone()

            # Create a user object that mimics the SQLAlchemy model structure
            class UserObject:
                def __init__(self, data):
                    self.school_id = data.get("school_id")
                    self.role = data.get("role")
                    self.id = data.get("id")
                    self.created_at = data.get("created_at")

                    # Add student profile data if available
                    if student_data:

                        class StudentProfile:
                            def __init__(self, data):
                                self.course = data.get("course")
                                self.track = data.get("track")
                                self.year_level = data.get("year_level")
                                self.section = data.get("section")
                                self.id_front_path = data.get("id_front_path")
                                self.id_back_path = data.get("id_back_path")
                                self.face_photo_path = data.get("face_photo_path")
                                self.created_at = data.get("created_at")

                                # Add personal info if available
                                if data.get("first_name"):

                                    class PersonalInfo:
                                        def __init__(self, data):
                                            self.first_name = data.get("first_name")
                                            self.last_name = data.get("last_name")
                                            self.middle_name = data.get("middle_name")
                                            self.email = data.get("email")
                                            self.full_name = self.get_full_name()

                                        def get_full_name(self):
                                            if self.middle_name:
                                                return f"{self.first_name} {self.middle_name} {self.last_name}"
                                            return f"{self.first_name} {self.last_name}"

                                    self.personal_info = PersonalInfo(data)

                            def get_full_name(self):
                                if hasattr(self, "personal_info"):
                                    return self.personal_info.full_name
                                return f"Student {self.id}"

                        self.student_profile = StudentProfile(student_data)
                    else:
                        self.student_profile = None

            user = UserObject(user_data)

    except Exception as e:
        logger.error(f"Database error during student dashboard: {str(e)}")
        session.clear()
        flash("Session expired. Please log in again.", "error")
        return redirect(url_for("login"))

    logger.info(f"Student dashboard accessed by {session.get('school_id')}")
    return render_template("student_dashboard.html", user=user)


@app.route("/instructor-dashboard")
@login_required
def instructor_dashboard():
    if session.get("role") != "instructor":
        session.clear()
        flash("Unauthorized access.", "error")
        return redirect(url_for("login"))

    # Get user data from database
    try:
        with get_db_connection().cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE id = %s", (session["user_id"],))
            user = cursor.fetchone()
    except Exception as e:
        logger.error(f"Database error during instructor dashboard: {str(e)}")
        session.clear()
        flash("Session expired. Please log in again.", "error")
        return redirect(url_for("login"))

    if not user:
        session.clear()
        flash("Session expired. Please log in again.", "error")
        return redirect(url_for("login"))

    logger.info(f"Instructor dashboard accessed by {session.get('school_id')}")
    return render_template("instructor_dashboard.html", user=user)


@app.route("/admin-dashboard")
@login_required
def admin_dashboard():
    if session.get("role") != "admin":
        session.clear()
        flash("Unauthorized access.", "error")
        return redirect(url_for("login"))

    # Get user data from database
    try:
        with get_db_connection().cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE id = %s", (session["user_id"],))
            user = cursor.fetchone()
    except Exception as e:
        logger.error(f"Database error during admin dashboard: {str(e)}")
        session.clear()
        flash("Session expired. Please log in again.", "error")
        return redirect(url_for("login"))

    if not user:
        session.clear()
        flash("Session expired. Please log in again.", "error")
        return redirect(url_for("login"))

    logger.info(f"Admin dashboard accessed by {session.get('school_id')}")
    return render_template("admin_dashboard.html", user=user)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        logger.info("Registration form submitted")

        school_id = request.form.get("schoolId", "").strip()
        course = request.form.get("course", "").strip()
        track = request.form.get("track", "").strip() or None
        year_level = request.form.get("yearLevel", "").strip()
        section = request.form.get("section", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirmPassword", "")

        # Validation
        errors = []

        # Check if school ID already exists
        try:
            with get_db_connection().cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM users WHERE school_id = %s", (school_id,)
                )
                existing_user = cursor.fetchone()
        except Exception as e:
            logger.error(f"Database error during registration check: {str(e)}")
            flash("An error occurred. Please try again.", "error")
            return render_template("register.html")

        if existing_user:
            errors.append("School ID already registered")
            logger.warning(f"Registration failed: School ID {school_id} already exists")

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
                flash(error, "error")
            logger.warning(
                f"Registration validation failed for school ID {school_id}: {errors}"
            )
            return render_template(
                "register.html",
                form_data={
                    "schoolId": school_id,
                    "course": course,
                    "track": track,
                    "yearLevel": year_level,
                    "section": section,
                },
            )

        try:
            # Create user
            password_hash = generate_password_hash(password)

            with get_db_connection().cursor() as cursor:
                cursor.execute(
                    "INSERT INTO users (school_id, password_hash, role) VALUES (%s, %s, %s)",
                    (school_id, password_hash, "student"),
                )
                user_id = cursor.lastrowid

                # Create personal information record for student
                cursor.execute(
                    "INSERT INTO personal_info (first_name, last_name, email) VALUES (%s, %s, %s)",
                    ("Student", "User", f"{school_id}@student.edu"),
                )
                personal_info_id = cursor.lastrowid

                # Create student profile
                cursor.execute(
                    "INSERT INTO students (user_id, personal_info_id, course, track, year_level, section) VALUES (%s, %s, %s, %s, %s, %s)",
                    (
                        user_id,
                        personal_info_id,
                        course,
                        track,
                        int(year_level),
                        section,
                    ),
                )

            get_db_connection().commit()

            logger.info(f"User registered successfully: {school_id}")
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("login"))

        except Exception as e:
            get_db_connection().rollback()
            logger.error(f"Registration failed for {school_id}: {str(e)}")
            flash("Registration failed. Please try again.", "error")
            return render_template(
                "register.html",
                form_data={
                    "schoolId": school_id,
                    "course": course,
                    "track": track,
                    "yearLevel": year_level,
                    "section": section,
                },
            )

    logger.info("Registration page accessed")
    return render_template("register.html")


# Instructor Class Management Routes
@app.route("/instructor/classes")
@login_required
def instructor_classes():
    """Display instructor's class management page."""
    if session.get("role") != "instructor":
        flash("Access denied. Instructor privileges required.", "error")
        return redirect(url_for("home"))

    logger.info(f"Instructor {session.get('school_id')} accessed class management")
    return render_template("instructor_classes.html")


@app.route("/api/instructor/classes", methods=["GET"])
@login_required
def get_instructor_classes():
    """Get all classes for the logged-in instructor."""
    if session.get("role") != "instructor":
        return jsonify({"error": "Access denied"}), 403

    try:
        with get_db_connection().cursor() as cursor:
            # Get instructor ID
            cursor.execute(
                "SELECT id FROM instructors WHERE user_id = %s", (session["user_id"],)
            )
            instructor = cursor.fetchone()

            if not instructor:
                return jsonify({"error": "Instructor profile not found"}), 404

            # Get all classes for this instructor
            cursor.execute(
                "SELECT * FROM classes WHERE instructor_id = %s", (instructor["id"],)
            )
            classes = cursor.fetchall()

            classes_data = []
            for cls in classes:
                # Count members (students enrolled in this class)
                cursor.execute(
                    "SELECT COUNT(*) as count FROM student_classes WHERE class_id = %s",
                    (cls["id"],),
                )
                member_count = cursor.fetchone()["count"]

                # Compute class_id (formatted display name)
                formatted_year = cls["year"][-2:] if cls["year"] else "XX"
                formatted_semester = (
                    "1"
                    if cls["semester"] and "1st" in cls["semester"].lower()
                    else (
                        "2"
                        if cls["semester"] and "2nd" in cls["semester"].lower()
                        else "1"
                    )
                )
                computed_class_id = f"{formatted_year}-{formatted_semester} {cls['course']} {cls['section']}"

                classes_data.append(
                    {
                        "id": cls["id"],
                        "classType": cls["class_type"],
                        "year": cls["year"],
                        "semester": cls["semester"],
                        "course": cls["course"],
                        "track": cls["track"],
                        "section": cls["section"],
                        "schedule": cls["schedule"],
                        "class_id": computed_class_id,
                        "class_code": cls["class_code"],
                        "join_code": cls["join_code"],
                        "member_count": member_count,
                        "created_at": (
                            cls["created_at"].isoformat() if cls["created_at"] else None
                        ),
                        "updated_at": (
                            cls["updated_at"].isoformat() if cls["updated_at"] else None
                        ),
                    }
                )

        logger.info(
            f"Retrieved {len(classes_data)} classes for instructor {session.get('school_id')}"
        )
        return jsonify({"classes": classes_data})

    except Exception as e:
        logger.error(f"Failed to get classes: {str(e)}")
        return jsonify({"error": "Failed to retrieve classes"}), 500


@app.route("/api/instructor/classes", methods=["POST"])
@login_required
def create_class():
    """Create a new class for the logged-in instructor."""
    if session.get("role") != "instructor":
        return jsonify({"error": "Access denied"}), 403

    try:
        with get_db_connection().cursor() as cursor:
            # Get instructor ID
            cursor.execute(
                "SELECT id FROM instructors WHERE user_id = %s", (session["user_id"],)
            )
            instructor = cursor.fetchone()

            if not instructor:
                return jsonify({"error": "Instructor profile not found"}), 404

            data = request.get_json()

            # Validate required fields
            required_fields = [
                "classType",
                "year",
                "semester",
                "course",
                "track",
                "section",
                "schedule",
            ]
            for field in required_fields:
                if not data.get(field):
                    return jsonify({"error": f"{field} is required"}), 400

            # Validate classType
            if data.get("classType") not in ["MINOR", "MAJOR"]:
                return (
                    jsonify({"error": "classType must be either MINOR or MAJOR"}),
                    400,
                )

            # Validate section format (should be like "1A", "2B", etc.)
            section = data["section"]
            if not (
                len(section) == 2 and section[0].isdigit() and section[1].isalpha()
            ):
                return (
                    jsonify(
                        {"error": 'Section must be in format like "1A", "2B", etc.'}
                    ),
                    400,
                )

            # Generate unique class codes
            class_code, join_code = generate_class_codes()

            # Ensure join_code is unique
            cursor.execute("SELECT id FROM classes WHERE join_code = %s", (join_code,))
            while cursor.fetchone():
                class_code, join_code = generate_class_codes()
                cursor.execute(
                    "SELECT id FROM classes WHERE join_code = %s", (join_code,)
                )

            # Create new class
            cursor.execute(
                """INSERT INTO classes
                (instructor_id, class_type, year, semester, course, track, section, schedule, class_code, join_code)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    instructor["id"],
                    data["classType"],
                    data["year"],
                    data["semester"],
                    data["course"],
                    data["track"],
                    section,
                    data["schedule"],
                    class_code,
                    join_code,
                ),
            )

            class_id = cursor.lastrowid
            get_db_connection().commit()

            logger.info(
                f"Instructor {session.get('school_id')} created class: {data['year']}-{data['semester']} {data['course']} {section}"
            )
            return jsonify(
                {
                    "success": True,
                    "message": "Class created successfully",
                    "class": {
                        "id": class_id,
                        "classType": data["classType"],
                        "year": data["year"],
                        "semester": data["semester"],
                        "course": data["course"],
                        "track": data["track"],
                        "section": section,
                        "schedule": data["schedule"],
                        "class_id": f"{data['year'][-2:]}-{('1' if '1st' in data['semester'].lower() else '2')} {data['course']} {section}",
                        "class_code": class_code,
                        "join_code": join_code,
                    },
                }
            )

    except Exception as e:
        get_db_connection().rollback()
        logger.error(
            f"Failed to create class for instructor {session.get('school_id')}: {str(e)}"
        )
        return jsonify({"error": "Failed to create class"}), 500


# Student Class Management Routes
@app.route("/api/student/join-class", methods=["POST"])
@login_required
def join_class():
    """Join a class using join code."""
    if session.get("role") != "student":
        return jsonify({"error": "Access denied. Student privileges required."}), 403

    try:
        with get_db_connection().cursor() as cursor:
            # Get student ID
            cursor.execute(
                "SELECT id FROM students WHERE user_id = %s", (session["user_id"],)
            )
            student = cursor.fetchone()

            if not student:
                return jsonify({"error": "Student profile not found"}), 404

            data = request.get_json()
            join_code = data.get("join_code", "").strip().upper()

            if not join_code:
                return jsonify({"error": "Join code is required"}), 400

            if len(join_code) != 6:
                return jsonify({"error": "Join code must be 6 characters"}), 400

            # Step 1: First validate that the class exists
            cursor.execute("SELECT * FROM classes WHERE join_code = %s", (join_code,))
            class_obj = cursor.fetchone()

            if not class_obj:
                return jsonify({"error": "Invalid join code. Class not found."}), 404

            # Step 2: Check if student is already enrolled
            cursor.execute(
                "SELECT id FROM student_classes WHERE student_id = %s AND class_id = %s",
                (student["id"], class_obj["id"]),
            )
            existing_enrollment = cursor.fetchone()

            if existing_enrollment:
                # Return specific info about the existing enrollment
                return (
                    jsonify(
                        {
                            "error": "You are already enrolled in this class",
                            "already_enrolled": True,
                            "class_info": {
                                "class_id": f"{class_obj['year'][-2:] if class_obj['year'] else 'XX'}-{('1' if '1st' in (class_obj['semester'] or '').lower() else '2')} {class_obj['course']} {class_obj['section']}",
                                "course": class_obj["course"],
                                "section": class_obj["section"],
                                "schedule": class_obj["schedule"],
                            },
                        }
                    ),
                    400,
                )

            # Create enrollment
            cursor.execute(
                "INSERT INTO student_classes (student_id, class_id) VALUES (%s, %s)",
                (student["id"], class_obj["id"]),
            )
            get_db_connection().commit()

            # Compute class_id for logging (same format as used elsewhere)
            formatted_year = class_obj["year"][-2:] if class_obj["year"] else "XX"
            formatted_semester = (
                "1"
                if class_obj["semester"] and "1st" in class_obj["semester"].lower()
                else (
                    "2"
                    if class_obj["semester"] and "2nd" in class_obj["semester"].lower()
                    else "1"
                )
            )
            computed_class_id = f"{formatted_year}-{formatted_semester} {class_obj['course']} {class_obj['section']}"

            logger.info(
                f"Student {session.get('school_id')} joined class: {computed_class_id}"
            )
            # Notify listeners
            try:
                emit_live_version_update(int(class_obj["id"]))
            except Exception as _e:
                logger.warning(f"Emit after join class failed: {str(_e)}")
            return jsonify(
                {
                    "success": True,
                    "message": f"Successfully joined class: {computed_class_id}",
                    "class": {
                        "id": class_obj["id"],
                        "class_id": computed_class_id,
                        "course": class_obj["course"],
                        "section": class_obj["section"],
                        "schedule": class_obj["schedule"],
                    },
                }
            )

    except Exception as e:
        get_db_connection().rollback()
        logger.error(
            f"Failed to join class for student {session.get('school_id')}: {str(e)}"
        )
        return jsonify({"error": "Failed to join class"}), 500


@app.route("/api/student/joined-classes", methods=["GET"])
@login_required
def get_joined_classes():
    """Get all classes joined by the logged-in student."""
    if session.get("role") != "student":
        return jsonify({"error": "Access denied. Student privileges required."}), 403

    try:
        with get_db_connection().cursor() as cursor:
            # Get student ID
            cursor.execute(
                "SELECT id FROM students WHERE user_id = %s", (session["user_id"],)
            )
            student = cursor.fetchone()

            if not student:
                return jsonify({"error": "Student profile not found"}), 404

            # Get all enrollments for this student
            cursor.execute(
                """SELECT c.*, sc.joined_at FROM classes c
                JOIN student_classes sc ON c.id = sc.class_id
                WHERE sc.student_id = %s""",
                (student["id"],),
            )
            enrollments = cursor.fetchall()

            classes_data = []
            for enrollment in enrollments:
                # Compute class_id (formatted display name)
                formatted_year = enrollment["year"][-2:] if enrollment["year"] else "XX"
                formatted_semester = (
                    "1"
                    if enrollment["semester"]
                    and "1st" in enrollment["semester"].lower()
                    else (
                        "2"
                        if enrollment["semester"]
                        and "2nd" in enrollment["semester"].lower()
                        else "1"
                    )
                )
                computed_class_id = f"{formatted_year}-{formatted_semester} {enrollment['course']} {enrollment['section']}"

                classes_data.append(
                    {
                        "id": enrollment["id"],
                        "class_id": computed_class_id,
                        "year": enrollment["year"],
                        "semester": enrollment["semester"],
                        "course": enrollment["course"],
                        "track": enrollment["track"],
                        "section": enrollment["section"],
                        "schedule": enrollment["schedule"],
                        "class_code": enrollment["class_code"],
                        "join_code": enrollment["join_code"],
                        "instructor_name": "Instructor",  # Simplified for now
                        "joined_at": (
                            enrollment["joined_at"].isoformat()
                            if enrollment["joined_at"]
                            else None
                        ),
                    }
                )

        logger.info(
            f"Retrieved {len(classes_data)} joined classes for student {session.get('school_id')}"
        )
        return jsonify({"classes": classes_data})

    except Exception as e:
        logger.error(f"Failed to get joined classes: {str(e)}")
        return jsonify({"error": "Failed to retrieve joined classes"}), 500


@app.route("/admin/create-instructor", methods=["POST"])
@login_required
def create_instructor():
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Unauthorized"}), 403

    try:
        data = request.get_json()

        # Personal Information
        first_name = data.get("firstName", "").strip()
        last_name = data.get("lastName", "").strip()
        middle_name = data.get("middleName", "").strip()
        email = data.get("email", "").strip()
        phone = data.get("phone", "").strip()
        address = data.get("address", "").strip()
        birth_date = data.get("birthDate")
        gender = data.get("gender", "").strip()
        emergency_contact_name = data.get("emergencyContactName", "").strip()
        emergency_contact_phone = data.get("emergencyContactPhone", "").strip()

        # Account Information
        school_id = data.get("schoolId", "").strip()
        password = data.get("password", "")
        employee_id = data.get("employeeId", "").strip()

        # Professional Information
        department = data.get("department", "").strip()
        specialization = data.get("specialization", "").strip()

        # Validation
        errors = []

        # Check if school ID already exists
        try:
            with get_db_connection().cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM users WHERE school_id = %s", (school_id,)
                )
                existing_user = cursor.fetchone()
        except Exception as e:
            logger.error(f"Database error during instructor creation check: {str(e)}")
            return jsonify({"success": False, "message": "Database error"}), 500

        if existing_user:
            errors.append("School ID already exists")

        # Validate required fields
        if not first_name:
            errors.append("First name is required")
        if not last_name:
            errors.append("Last name is required")
        if not email:
            errors.append("Email is required")
        if not school_id:
            errors.append("School ID is required")
        if not password:
            errors.append("Password is required")
        if not department:
            errors.append("Department is required")

        # Password strength validation
        if len(password) < 6:
            errors.append("Password must be at least 6 characters long")
        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number")

        # Email validation
        import re

        email_regex = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
        if email and not re.match(email_regex, email):
            errors.append("Please enter a valid email address")

        if errors:
            logger.warning(f"Instructor creation failed: {errors}")
            return jsonify({"success": False, "message": "; ".join(errors)}), 400

        try:
            # Create personal information record
            with get_db_connection().cursor() as cursor:
                cursor.execute(
                    """INSERT INTO personal_info
                    (first_name, last_name, middle_name, email, phone, address, birth_date, gender, emergency_contact_name, emergency_contact_phone)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (
                        first_name,
                        last_name,
                        middle_name if middle_name else None,
                        email,
                        phone if phone else None,
                        address if address else None,
                        (
                            datetime.strptime(birth_date, "%Y-%m-%d").date()
                            if birth_date
                            else None
                        ),
                        gender if gender else None,
                        emergency_contact_name if emergency_contact_name else None,
                        emergency_contact_phone if emergency_contact_phone else None,
                    ),
                )
                personal_info_id = cursor.lastrowid

                # Create instructor user
                password_hash = generate_password_hash(password)
                cursor.execute(
                    "INSERT INTO users (school_id, password_hash, role) VALUES (%s, %s, %s)",
                    (school_id, password_hash, "instructor"),
                )
                user_id = cursor.lastrowid

                # Create instructor profile
                cursor.execute(
                    """INSERT INTO instructors
                    (user_id, personal_info_id, department, specialization, employee_id)
                    VALUES (%s, %s, %s, %s, %s)""",
                    (
                        user_id,
                        personal_info_id,
                        department,
                        specialization if specialization else None,
                        employee_id if employee_id else None,
                    ),
                )

            get_db_connection().commit()

            logger.info(
                f"Instructor created successfully: {first_name} {last_name} ({school_id}) by admin {session.get('school_id')}"
            )
            return jsonify(
                {
                    "success": True,
                    "message": f"Instructor {first_name} {last_name} created successfully!",
                    "instructor": {
                        "school_id": school_id,
                        "name": f"{first_name} {last_name}",
                        "email": email,
                        "department": department,
                        "specialization": specialization,
                        "employee_id": employee_id,
                    },
                }
            )

        except Exception as e:
            get_db_connection().rollback()
            logger.error(f"Instructor creation failed: {str(e)}")
            return (
                jsonify(
                    {"success": False, "message": "Failed to create instructor account"}
                ),
                500,
            )

    except Exception as e:
        logger.error(f"Instructor creation error: {str(e)}")
        return jsonify({"success": False, "message": "Invalid request data"}), 400


@app.route("/api/admin/instructors", methods=["GET"])
@login_required
def get_instructors():
    """Get all instructors with analytics data."""
    if session.get("role") != "admin":
        return jsonify({"error": "Access denied. Admin privileges required."}), 403

    try:
        with get_db_connection().cursor() as cursor:
            # Get all instructors with their related data
            cursor.execute(
                """SELECT i.*, u.school_id, pi.first_name, pi.last_name, pi.email
                FROM instructors i
                JOIN users u ON i.user_id = u.id
                LEFT JOIN personal_info pi ON i.personal_info_id = pi.id"""
            )
            instructors = cursor.fetchall()

            instructors_data = []
            active_count = 0
            suspended_count = 0

            for instructor in instructors:
                instructor_data = {
                    "id": instructor["id"],
                    "school_id": instructor["school_id"],
                    "name": f"{instructor['first_name'] or ''} {instructor['last_name'] or ''}".strip()
                    or f"Instructor {instructor['id']}",
                    "email": instructor["email"] or "N/A",
                    "department": instructor["department"] or "Not specified",
                    "specialization": instructor["specialization"] or "Not specified",
                    "employee_id": instructor["employee_id"] or "Not specified",
                    "status": instructor["status"] or "active",
                    "hire_date": (
                        instructor["hire_date"].isoformat()
                        if instructor["hire_date"]
                        else None
                    ),
                    "created_at": (
                        instructor["created_at"].isoformat()
                        if instructor["created_at"]
                        else None
                    ),
                    "class_count": 0,  # Will be calculated below
                }

                if instructor_data["status"] == "active":
                    active_count += 1
                else:
                    suspended_count += 1

                instructors_data.append(instructor_data)

            # Get recent instructors (last 5)
            recent_instructors = sorted(
                instructors_data, key=lambda x: x["created_at"] or "", reverse=True
            )[:5]

            analytics = {
                "total_instructors": len(instructors_data),
                "active_instructors": active_count,
                "suspended_instructors": suspended_count,
                "recent_instructors": recent_instructors,
            }

        logger.info(f"Admin {session.get('school_id')} retrieved instructor analytics")
        return jsonify(
            {"success": True, "instructors": instructors_data, "analytics": analytics}
        )

    except Exception as e:
        logger.error(f"Failed to get instructors: {str(e)}")
        return jsonify({"error": "Failed to retrieve instructors"}), 500


@app.route("/api/admin/instructors/<int:instructor_id>", methods=["GET"])
@login_required
def get_instructor_details(instructor_id):
    """Get detailed information about a specific instructor."""
    if session.get("role") != "admin":
        return jsonify({"error": "Access denied. Admin privileges required."}), 403

    try:
        with get_db_connection().cursor() as cursor:
            # Get instructor with all related data
            cursor.execute(
                """SELECT i.id, i.user_id, i.personal_info_id, i.department, i.specialization,
                         i.employee_id, i.hire_date, i.status, i.created_at, i.updated_at,
                         u.school_id, u.role,
                         pi.first_name, pi.last_name, pi.middle_name, pi.email, pi.phone,
                         pi.address, pi.birth_date, pi.gender, pi.emergency_contact_name,
                         pi.emergency_contact_phone
                FROM instructors i
                JOIN users u ON i.user_id = u.id
                LEFT JOIN personal_info pi ON i.personal_info_id = pi.id
                WHERE i.id = %s""",
                (instructor_id,),
            )
            instructor = cursor.fetchone()

            if not instructor:
                return jsonify({"error": "Instructor not found"}), 404

            # Get instructor's classes
            cursor.execute(
                """SELECT id, year, semester, course, section, schedule, class_code, join_code, created_at
                FROM classes WHERE instructor_id = %s""",
                (instructor_id,),
            )
            classes = cursor.fetchall()

            # Format class_id for each class (computed property)
            for cls in classes:
                formatted_year = cls["year"][-2:] if cls["year"] else "XX"
                formatted_semester = (
                    "1"
                    if cls["semester"] and "1st" in cls["semester"].lower()
                    else (
                        "2"
                        if cls["semester"] and "2nd" in cls["semester"].lower()
                        else "1"
                    )
                )
                cls["class_id"] = (
                    f"{formatted_year}-{formatted_semester} {cls['course']} {cls['section']}"
                )

            instructor_details = {
                "id": instructor["id"],
                "school_id": instructor["school_id"],
                "personal_info": {
                    "first_name": instructor["first_name"] or "N/A",
                    "last_name": instructor["last_name"] or "N/A",
                    "middle_name": instructor["middle_name"],
                    "email": instructor["email"] or "N/A",
                    "phone": instructor["phone"],
                    "address": instructor["address"],
                    "birth_date": (
                        instructor["birth_date"].isoformat()
                        if instructor["birth_date"]
                        else None
                    ),
                    "gender": instructor["gender"],
                    "emergency_contact_name": instructor["emergency_contact_name"],
                    "emergency_contact_phone": instructor["emergency_contact_phone"],
                },
                "professional_info": {
                    "department": instructor["department"],
                    "specialization": instructor["specialization"],
                    "employee_id": instructor["employee_id"],
                    "hire_date": (
                        instructor["hire_date"].isoformat()
                        if instructor["hire_date"]
                        else None
                    ),
                },
                "account_info": {
                    "status": instructor["status"] or "active",
                    "created_at": (
                        instructor["created_at"].isoformat()
                        if instructor["created_at"]
                        else None
                    ),
                    "updated_at": (
                        instructor["updated_at"].isoformat()
                        if instructor["updated_at"]
                        else None
                    ),
                },
                "statistics": {
                    "total_classes": len(classes),
                    "class_list": [
                        {
                            "id": cls["id"],
                            "class_id": cls["class_id"],
                            "course": cls["course"],
                            "section": cls["section"],
                            "year": cls["year"],
                            "semester": cls["semester"],
                        }
                        for cls in classes
                    ],
                },
            }

        logger.info(
            f"Admin {session.get('school_id')} viewed instructor details: {instructor['school_id']}"
        )
        return jsonify({"success": True, "instructor": instructor_details})

    except Exception as e:
        logger.error(f"Failed to get instructor details: {str(e)}")
        return jsonify({"error": "Failed to retrieve instructor details"}), 500


@app.route("/api/admin/instructors/<int:instructor_id>/status", methods=["PUT"])
@login_required
def update_instructor_status(instructor_id):
    """Suspend or unsuspend an instructor account."""
    if session.get("role") != "admin":
        return jsonify({"error": "Access denied. Admin privileges required."}), 403

    try:
        data = request.get_json()
        new_status = data.get("status")

        if new_status not in ["active", "suspended"]:
            return (
                jsonify({"error": "Invalid status. Must be 'active' or 'suspended'"}),
                400,
            )

        with get_db_connection().cursor() as cursor:
            # Check if instructor exists
            cursor.execute(
                "SELECT id, status FROM instructors WHERE id = %s", (instructor_id,)
            )
            instructor = cursor.fetchone()

            if not instructor:
                return jsonify({"error": "Instructor not found"}), 404

            old_status = instructor["status"] or "active"

            # Update instructor status
            cursor.execute(
                "UPDATE instructors SET status = %s WHERE id = %s",
                (new_status, instructor_id),
            )

        get_db_connection().commit()

        logger.info(
            f"Admin {session.get('school_id')} changed instructor status from {old_status} to {new_status}"
        )
        return jsonify(
            {
                "success": True,
                "message": f"Instructor {new_status} successfully",
                "instructor": {
                    "id": instructor_id,
                    "status": new_status,
                },
            }
        )

    except Exception as e:
        get_db_connection().rollback()
        logger.error(f"Failed to update instructor status: {str(e)}")
        return jsonify({"error": "Failed to update instructor status"}), 500


@app.route("/api/admin/instructors/<int:instructor_id>", methods=["DELETE"])
@login_required
def delete_instructor(instructor_id):
    """Delete an instructor account and all associated data."""
    if session.get("role") != "admin":
        return jsonify({"error": "Access denied. Admin privileges required."}), 403

    try:
        with get_db_connection().cursor() as cursor:
            # Check if instructor exists
            cursor.execute(
                "SELECT i.id, i.user_id, u.school_id FROM instructors i JOIN users u ON i.user_id = u.id WHERE i.id = %s",
                (instructor_id,),
            )
            instructor = cursor.fetchone()

            if not instructor:
                return jsonify({"error": "Instructor not found"}), 404

            # Check if instructor has active classes
            cursor.execute(
                "SELECT COUNT(*) as count FROM classes WHERE instructor_id = %s",
                (instructor_id,),
            )
            active_classes = cursor.fetchone()["count"]

            if active_classes > 0:
                return (
                    jsonify(
                        {
                            "error": f"Cannot delete instructor with {active_classes} active classes. Please reassign or delete classes first."
                        }
                    ),
                    400,
                )

            # Get personal info ID for deletion
            cursor.execute(
                "SELECT personal_info_id FROM instructors WHERE id = %s",
                (instructor_id,),
            )
            personal_info_result = cursor.fetchone()

            # Delete in proper order
            if personal_info_result and personal_info_result["personal_info_id"]:
                cursor.execute(
                    "DELETE FROM personal_info WHERE id = %s",
                    (personal_info_result["personal_info_id"],),
                )

            cursor.execute("DELETE FROM instructors WHERE id = %s", (instructor_id,))
            cursor.execute("DELETE FROM users WHERE id = %s", (instructor["user_id"],))

        get_db_connection().commit()

        logger.info(
            f"Admin {session.get('school_id')} deleted instructor: {instructor['school_id']}"
        )
        return jsonify({"success": True, "message": "Instructor deleted successfully"})

    except Exception as e:
        get_db_connection().rollback()
        logger.error(f"Failed to delete instructor: {str(e)}")
        return jsonify({"error": "Failed to delete instructor"}), 500


@app.route("/api/instructor/classes/<int:class_id>/members", methods=["GET"])
@login_required
def get_class_members(class_id):
    """Get all members (students) of a specific class."""
    if session.get("role") != "instructor":
        return jsonify({"error": "Access denied"}), 403

    try:
        with get_db_connection().cursor() as cursor:
            # Get instructor ID to verify ownership
            cursor.execute(
                "SELECT id FROM instructors WHERE user_id = %s", (session["user_id"],)
            )
            instructor = cursor.fetchone()

            if not instructor:
                return jsonify({"error": "Instructor profile not found"}), 404

            # Find the class and verify ownership
            cursor.execute(
                "SELECT * FROM classes WHERE id = %s AND instructor_id = %s",
                (class_id, instructor["id"]),
            )
            class_obj = cursor.fetchone()

            if not class_obj:
                return jsonify({"error": "Class not found or access denied"}), 404

            # Compute class_id (formatted display name)
            formatted_year = class_obj["year"][-2:] if class_obj["year"] else "XX"
            formatted_semester = (
                "1"
                if class_obj["semester"] and "1st" in class_obj["semester"].lower()
                else (
                    "2"
                    if class_obj["semester"] and "2nd" in class_obj["semester"].lower()
                    else "1"
                )
            )
            class_obj["class_id"] = (
                f"{formatted_year}-{formatted_semester} {class_obj['course']} {class_obj['section']}"
            )

            # Get all student enrollments for this class
            cursor.execute(
                """SELECT sc.*, s.id as student_id, s.course, s.track, s.year_level, s.section,
                          u.school_id, pi.first_name, pi.last_name, pi.middle_name
                FROM student_classes sc
                JOIN students s ON sc.student_id = s.id
                JOIN users u ON s.user_id = u.id
                LEFT JOIN personal_info pi ON s.personal_info_id = pi.id
                WHERE sc.class_id = %s""",
                (class_id,),
            )
            enrollments = cursor.fetchall()

            members = []
            for enrollment in enrollments:
                # Format student name
                first_name = enrollment.get("first_name", "")
                middle_name = enrollment.get("middle_name", "")
                last_name = enrollment.get("last_name", "")

                if first_name and last_name:
                    student_name = (
                        f"{first_name} {middle_name} {last_name}".strip()
                        if middle_name
                        else f"{first_name} {last_name}"
                    )
                else:
                    student_name = enrollment["school_id"]

                members.append(
                    {
                        "id": enrollment["student_id"],
                        "school_id": enrollment["school_id"],
                        "student_name": student_name,
                        "first_name": first_name,
                        "middle_name": middle_name,
                        "last_name": last_name,
                        "course": enrollment["course"],
                        "track": enrollment["track"],
                        "year_level": enrollment["year_level"],
                        "section": enrollment["section"],
                        "joined_at": (
                            enrollment["joined_at"].isoformat()
                            if enrollment["joined_at"]
                            else None
                        ),
                    }
                )

        logger.info(
            f"Instructor {session.get('school_id')} viewed {len(members)} members of class {class_obj['class_id']}"
        )
        return jsonify(
            {
                "class_id": class_obj["class_id"],
                "class_name": f"{class_obj['course']} {class_obj['section']}",
                "members": members,
                "total_members": len(members),
            }
        )

    except Exception as e:
        logger.error(f"Failed to get members for class {class_id}: {str(e)}")
        return jsonify({"error": "Failed to get class members"}), 500


@app.route("/api/instructor/classes/<int:class_id>/details", methods=["GET"])
@login_required
def get_class_details(class_id):
    """Get detailed information about a specific class."""
    if session.get("role") != "instructor":
        return jsonify({"error": "Access denied"}), 403

    try:
        with get_db_connection().cursor() as cursor:
            # Get instructor ID to verify ownership
            cursor.execute(
                "SELECT id FROM instructors WHERE user_id = %s", (session["user_id"],)
            )
            instructor = cursor.fetchone()

            if not instructor:
                return jsonify({"error": "Instructor profile not found"}), 404

            # Find the class and verify ownership
            cursor.execute(
                "SELECT * FROM classes WHERE id = %s AND instructor_id = %s",
                (class_id, instructor["id"]),
            )
            class_obj = cursor.fetchone()

            if not class_obj:
                return jsonify({"error": "Class not found or access denied"}), 404

            # Get instructor information
            cursor.execute(
                """SELECT i.*, pi.first_name, pi.last_name, pi.middle_name, pi.email
                FROM instructors i
                LEFT JOIN personal_info pi ON i.personal_info_id = pi.id
                WHERE i.id = %s""",
                (instructor["id"],),
            )
            instructor_info = cursor.fetchone()

            # Format instructor name
            instructor_name = ""
            if instructor_info:
                first_name = instructor_info.get("first_name", "")
                middle_name = instructor_info.get("middle_name", "")
                last_name = instructor_info.get("last_name", "")
                if first_name and last_name:
                    instructor_name = (
                        f"{first_name} {middle_name} {last_name}".strip()
                        if middle_name
                        else f"{first_name} {last_name}"
                    )
                else:
                    instructor_name = "Instructor"

            class_info = {
                "id": class_obj["id"],
                "year": class_obj["year"],
                "semester": class_obj["semester"],
                "course": class_obj["course"],
                "track": class_obj["track"],
                "section": class_obj["section"],
                "schedule": class_obj["schedule"],
                "class_code": class_obj["class_code"],
                "join_code": class_obj["join_code"],
                "grading_template_id": class_obj["grading_template_id"],
                "created_at": (
                    class_obj["created_at"].isoformat()
                    if class_obj["created_at"]
                    else None
                ),
                "updated_at": (
                    class_obj["updated_at"].isoformat()
                    if class_obj["updated_at"]
                    else None
                ),
            }

            instructor_details = {
                "full_name": instructor_name,
                "department": (
                    instructor_info.get("department", "N/A")
                    if instructor_info
                    else "N/A"
                ),
                "specialization": (
                    instructor_info.get("specialization") if instructor_info else None
                ),
                "email": (
                    instructor_info.get("email", "N/A") if instructor_info else "N/A"
                ),
            }

        logger.info(
            f"Instructor {session.get('school_id')} viewed details of class {class_id}"
        )
        return jsonify(
            {
                "class_info": class_info,
                "instructor_info": instructor_details,
            }
        )

    except Exception as e:
        logger.error(f"Failed to get details for class {class_id}: {str(e)}")
        return jsonify({"error": "Failed to get class details"}), 500


@app.route("/api/student/leave-class/<int:class_id>", methods=["DELETE"])
@login_required
def leave_class(class_id):
    """Leave a class (unenroll student from class)."""
    if session.get("role") != "student":
        return jsonify({"error": "Access denied. Student privileges required."}), 403

    try:
        with get_db_connection().cursor() as cursor:
            # Get student ID
            cursor.execute(
                "SELECT id FROM students WHERE user_id = %s", (session["user_id"],)
            )
            student = cursor.fetchone()

            if not student:
                return jsonify({"error": "Student profile not found"}), 404

            # Check if student is enrolled in this class
            cursor.execute(
                "SELECT id FROM student_classes WHERE student_id = %s AND class_id = %s",
                (student["id"], class_id),
            )
            enrollment = cursor.fetchone()

            if not enrollment:
                return jsonify({"error": "You are not enrolled in this class"}), 400

            # Get class info for logging
            cursor.execute(
                "SELECT year, semester, course, section FROM classes WHERE id = %s",
                (class_id,),
            )
            class_obj = cursor.fetchone()

            # Compute class_id for logging
            if class_obj:
                formatted_year = class_obj["year"][-2:] if class_obj["year"] else "XX"
                formatted_semester = (
                    "1"
                    if class_obj["semester"] and "1st" in class_obj["semester"].lower()
                    else (
                        "2"
                        if class_obj["semester"]
                        and "2nd" in class_obj["semester"].lower()
                        else "1"
                    )
                )
                computed_class_id = f"{formatted_year}-{formatted_semester} {class_obj['course']} {class_obj['section']}"
                class_obj["class_id"] = computed_class_id

            # Delete enrollment
            cursor.execute(
                "DELETE FROM student_classes WHERE student_id = %s AND class_id = %s",
                (student["id"], class_id),
            )

            # Verify deletion
            cursor.execute(
                "SELECT id FROM student_classes WHERE student_id = %s AND class_id = %s",
                (student["id"], class_id),
            )
            remaining_enrollment = cursor.fetchone()

            if remaining_enrollment:
                logger.error(
                    f"Failed to delete enrollment for student {student['id']} and class {class_id}"
                )
                return (
                    jsonify({"error": "Failed to leave class - please try again"}),
                    500,
                )

        get_db_connection().commit()

        class_name = (
            f"{class_obj['course']} {class_obj['section']}"
            if class_obj
            else "Unknown Class"
        )
        logger.info(
            f"Student {session.get('school_id')} left class: {class_obj['class_id'] if class_obj else 'Unknown'}"
        )

        # Notify listeners
        try:
            emit_live_version_update(int(class_id))
        except Exception as _e:
            logger.warning(f"Emit after leave class failed: {str(_e)}")

        return jsonify(
            {
                "success": True,
                "message": f"Successfully left class: {class_obj['class_id'] if class_obj else 'Unknown Class'}",
            }
        )

    except Exception as e:
        get_db_connection().rollback()
        logger.error(
            f"Failed to leave class for student {session.get('school_id')}: {str(e)}"
        )
        return jsonify({"error": "Failed to leave class"}), 500


@app.route("/gradebuilder")
def gradebuilder_entry():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "instructor":
        return render_template("unauthorized.html", message="Access denied.")

    return render_template("gradebuilder.html")


@app.route("/api/gradebuilder/data")
def gradebuilder_data():
    """Load instructor info, classes, and grade structures."""
    if "user_id" not in session:
        return jsonify({"error": "not_logged_in"}), 401

    if session.get("role") != "instructor":
        return jsonify({"error": "forbidden"}), 403

    user_id = session["user_id"]
    instructor_id = session.get("instructor_id")

    if not instructor_id:
        # Fetch instructor id in case not stored yet
        with get_db_connection().cursor() as cursor:
            cursor.execute("SELECT id FROM instructors WHERE user_id = %s", (user_id,))
            instructor = cursor.fetchone()
            if not instructor:
                return jsonify({"error": "instructor_not_found"}), 404
            instructor_id = instructor["id"]
            session["instructor_id"] = instructor_id

    # Fetch instructor info, classes, structures
    with get_db_connection().cursor() as cursor:
        # Instructor info
        cursor.execute(
            """
            SELECT CONCAT(p.first_name, ' ', p.last_name) AS name, p.email
            FROM instructors i
            LEFT JOIN personal_info p ON p.id = i.personal_info_id
            WHERE i.id = %s
        """,
            (instructor_id,),
        )
        instructor_info = cursor.fetchone()

        # Classes
        cursor.execute(
            """
            SELECT id AS class_id, course, section, class_code
            FROM classes
            WHERE instructor_id = %s
            ORDER BY course, section
        """,
            (instructor_id,),
        )
        classes = cursor.fetchall()

        # Grade Structures with versioning
        cursor.execute(
            """
            SELECT gs.id, gs.class_id, gs.structure_name, gs.structure_json,
                   gs.created_at, gs.updated_at, gs.version,
                   COUNT(gsh.id) as history_count
            FROM grade_structures gs
            LEFT JOIN grade_structure_history gsh ON gs.id = gsh.structure_id
            WHERE gs.class_id IN (
                SELECT id FROM classes WHERE instructor_id = %s
            )
            GROUP BY gs.id
            ORDER BY gs.updated_at DESC
        """,
            (instructor_id,),
        )
        structures = cursor.fetchall()

    return jsonify(
        {
            "instructor": instructor_info,
            "classes": classes,
            "structures": structures,
            "csrf_token": generate_csrf(),
        }
    )


@app.route("/api/gradebuilder/history/<int:structure_id>", methods=["GET"])
def gradebuilder_history(structure_id):
    """Get version history for a grading structure."""
    if "user_id" not in session or session.get("role") != "instructor":
        return jsonify({"error": "unauthorized"}), 403

    instructor_id = session.get("instructor_id")
    if not instructor_id:
        return jsonify({"error": "instructor_not_found"}), 404

    # Validate structure_id is positive integer
    if structure_id <= 0:
        return jsonify({"error": "invalid_structure_id"}), 400

    try:
        with get_db_connection().cursor() as cursor:
            # Check if structure exists and belongs to instructor
            cursor.execute(
                "SELECT id FROM grade_structures WHERE id = %s AND created_by = %s",
                (structure_id, instructor_id),
            )
            if not cursor.fetchone():
                return jsonify({"error": "structure_not_found_or_unauthorized"}), 404

            # Get history
            cursor.execute(
                """
                SELECT id, structure_json, version, changed_at
                FROM grade_structure_history
                WHERE structure_id = %s
                ORDER BY version DESC
                """,
                (structure_id,),
            )
            history = cursor.fetchall()

        history_data = []
        for entry in history:
            history_data.append(
                {
                    "id": entry["id"],
                    "version": entry["version"],
                    "structure": json.loads(entry["structure_json"]),
                    "changed_at": (
                        entry["changed_at"].isoformat() if entry["changed_at"] else None
                    ),
                }
            )

        return jsonify({"success": True, "history": history_data}), 200

    except Exception as e:
        logger.error(f"Failed to get history for structure {structure_id}: {str(e)}")
        return jsonify({"success": False, "error": "Failed to get history"}), 500


@app.route(
    "/api/gradebuilder/restore/<int:structure_id>/<int:history_id>", methods=["POST"]
)
def gradebuilder_restore(structure_id, history_id):
    """Restore a grading structure from history."""
    if "user_id" not in session or session.get("role") != "instructor":
        return jsonify({"error": "unauthorized"}), 403

    instructor_id = session.get("instructor_id")
    if not instructor_id:
        return jsonify({"error": "instructor_not_found"}), 404

    # Validate IDs
    if structure_id <= 0 or history_id <= 0:
        return jsonify({"error": "invalid_id"}), 400

    try:
        with get_db_connection().cursor() as cursor:
            # Check if structure exists and belongs to instructor
            cursor.execute(
                "SELECT id FROM grade_structures WHERE id = %s AND created_by = %s",
                (structure_id, instructor_id),
            )
            if not cursor.fetchone():
                return jsonify({"error": "structure_not_found_or_unauthorized"}), 404

            # Get history entry
            cursor.execute(
                "SELECT structure_json, version FROM grade_structure_history WHERE id = %s AND structure_id = %s",
                (history_id, structure_id),
            )
            history_entry = cursor.fetchone()
            if not history_entry:
                return jsonify({"error": "history_entry_not_found"}), 404

            # Save current state to history before restoring
            cursor.execute(
                "SELECT structure_json, version FROM grade_structures WHERE id = %s",
                (structure_id,),
            )
            current = cursor.fetchone()

            now = datetime.now()
            new_version = current["version"] + 1

            cursor.execute(
                """
                INSERT INTO grade_structure_history
                    (structure_id, structure_json, version, changed_by, changed_at)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    structure_id,
                    current["structure_json"],
                    current["version"],
                    instructor_id,
                    now,
                ),
            )

            # Restore from history
            cursor.execute(
                """
                UPDATE grade_structures
                SET structure_json = %s, version = %s, updated_at = %s
                WHERE id = %s AND created_by = %s
                """,
                (
                    history_entry["structure_json"],
                    new_version,
                    now,
                    structure_id,
                    instructor_id,
                ),
            )

        get_db_connection().commit()
        # Emit version update for this class
        try:
            with get_db_connection().cursor() as cursor:
                cursor.execute(
                    "SELECT class_id FROM grade_structures WHERE id = %s",
                    (structure_id,),
                )
                row = cursor.fetchone()
                if row:
                    emit_live_version_update(int(row["class_id"]))
        except Exception as _e:
            logger.warning(f"Emit after restore failed: {str(_e)}")
        logger.info(
            f"Instructor {session.get('school_id')} restored structure {structure_id} to version {history_entry['version']}"
        )
        return (
            jsonify(
                {
                    "success": True,
                    "message": f"Structure restored to version {history_entry['version']}",
                }
            ),
            200,
        )

    except Exception as e:
        get_db_connection().rollback()
        logger.error(
            f"Failed to restore structure {structure_id} from history {history_id}: {str(e)}"
        )
        return jsonify({"success": False, "error": "Failed to restore structure"}), 500


@app.route("/api/gradebuilder/delete/<int:structure_id>", methods=["DELETE"])
def gradebuilder_delete(structure_id):
    """Delete a grading structure."""

    print("\n=== [DELETE REQUEST RECEIVED] ===")
    print(f"Structure ID: {structure_id}")
    print(f"Session Info: {dict(session)}")

    # Session and role check
    if "user_id" not in session or session.get("role") != "instructor":
        print("[ERROR] Unauthorized access attempt.")
        return jsonify({"error": "unauthorized"}), 403

    instructor_id = session.get("instructor_id")
    if not instructor_id:
        print("[ERROR] Instructor ID not found in session.")
        return jsonify({"error": "instructor_not_found"}), 404

    # Validate structure_id
    if structure_id <= 0:
        print("[ERROR] Invalid structure_id received.")
        return jsonify({"error": "invalid_structure_id"}), 400

    conn = get_db_connection()
    affected_class_id = None
    try:
        with conn.cursor() as cursor:
            print(
                f"[DB] Checking if structure {structure_id} belongs to instructor {instructor_id}..."
            )
            cursor.execute(
                "SELECT id, class_id FROM grade_structures WHERE id = %s AND created_by = %s",
                (structure_id, instructor_id),
            )
            row = cursor.fetchone()

            if not row:
                print("[DB] Structure not found or instructor mismatch.")
                return jsonify({"error": "structure_not_found_or_unauthorized"}), 404

            affected_class_id = row.get("class_id")
            # Delete related history (optional if cascade)
            print(f"[DB] Deleting history for structure {structure_id}...")
            cursor.execute(
                "DELETE FROM grade_structure_history WHERE structure_id = %s",
                (structure_id,),
            )

            # Delete main structure
            print(f"[DB] Deleting grade structure {structure_id}...")
            cursor.execute(
                "DELETE FROM grade_structures WHERE id = %s AND created_by = %s",
                (structure_id, instructor_id),
            )

        conn.commit()
        print("[SUCCESS] Structure deleted successfully.")
        logger.info(
            f"Instructor {session.get('school_id')} deleted grade structure {structure_id}"
        )

        # Emit version update
        try:
            if affected_class_id:
                emit_live_version_update(int(affected_class_id))
        except Exception as _e:
            logger.warning(f"Emit after delete failed: {str(_e)}")

        return (
            jsonify({"success": True, "message": "Structure deleted successfully"}),
            200,
        )

    except Exception as e:
        conn.rollback()
        print(f"[EXCEPTION] {str(e)}")
        logger.error(
            f"Failed to delete grade structure {structure_id} for instructor {session.get('school_id')}: {str(e)}"
        )
        return jsonify({"success": False, "error": str(e)}), 500

    finally:
        conn.close()
        print("[CLOSE] Database connection closed.\n")


@app.route("/api/gradebuilder/save", methods=["POST"])
def gradebuilder_save():
    """Save or create a grading structure."""
    logger.info(f"Gradebuilder save request received: {request.method} {request.path}")
    logger.info(f"Request headers: {dict(request.headers)}")

    if "user_id" not in session or session.get("role") != "instructor":
        logger.warning("Gradebuilder save: unauthorized access attempt")
        return jsonify({"error": "unauthorized"}), 403

    data = request.get_json()
    logger.info(f"Request data: {data}")
    if not data:
        logger.warning("Gradebuilder save: invalid payload - no data")
        return jsonify({"error": "invalid_payload"}), 400

    instructor_id = session.get("instructor_id")
    if not instructor_id:
        return jsonify({"error": "instructor_not_found"}), 404

    class_id = data.get("class_id")
    structure_name = data.get("structure_name", "Untitled Structure")
    structure_json_str = data.get("structure_json", "{}")

    logger.info(
        f"Parsed data - class_id: {class_id} (type: {type(class_id)}), structure_name: {structure_name}"
    )

    # Input validation and sanitization - handle string class_id
    try:
        if isinstance(class_id, str):
            class_id = int(class_id)
        elif not isinstance(class_id, int):
            raise ValueError("class_id must be int or string convertible to int")
    except (ValueError, TypeError):
        logger.warning(f"Invalid class_id: {class_id} (type: {type(class_id)})")
        return jsonify({"error": "invalid_class_id"}), 400

    if class_id <= 0:
        logger.warning(f"Invalid class_id value: {class_id}")
        return jsonify({"error": "invalid_class_id"}), 400

    if not isinstance(structure_name, str) or len(structure_name.strip()) == 0:
        return jsonify({"error": "invalid_structure_name"}), 400

    if len(structure_name) > 255:
        return jsonify({"error": "structure_name_too_long"}), 400

    # Sanitize structure_name
    structure_name = structure_name.strip()

    # Validate structure_json is a string and parse it
    if not isinstance(structure_json_str, str):
        return jsonify({"error": "invalid_structure_json"}), 400

    try:
        structure_json = json.loads(structure_json_str)
    except (TypeError, ValueError):
        return jsonify({"error": "invalid_structure_json_format"}), 400

    # Validate structure_json has required keys
    if not isinstance(structure_json, dict):
        return jsonify({"error": "structure_json_must_be_object"}), 400

    # Detailed schema validation
    is_valid, val_errors = validate_structure_json(structure_json)
    if not is_valid:
        return (
            jsonify({"error": "invalid_structure_schema", "details": val_errors}),
            400,
        )

    now = datetime.now()

    # Validate instructor owns this class
    with get_db_connection().cursor() as cursor:
        cursor.execute(
            "SELECT id FROM classes WHERE id = %s AND instructor_id = %s",
            (class_id, instructor_id),
        )
        if not cursor.fetchone():
            return jsonify({"error": "unauthorized_class"}), 403

    # Check if there's already a structure for this class (update) or create new
    with get_db_connection().cursor() as cursor:
        cursor.execute(
            "SELECT id, structure_json, version FROM grade_structures WHERE class_id = %s AND created_by = %s",
            (class_id, instructor_id),
        )
        existing_structure = cursor.fetchone()

    if existing_structure:
        # Update existing structure
        structure_id = existing_structure["id"]
        logger.info(f"Updating existing structure {structure_id} for class {class_id}")
        # Validate structure_id
        if not isinstance(structure_id, int) or structure_id <= 0:
            return jsonify({"error": "invalid_structure_id"}), 400

        # Get current structure for versioning
        with get_db_connection().cursor() as cursor:
            cursor.execute(
                "SELECT structure_json, version FROM grade_structures WHERE id = %s AND created_by = %s",
                (structure_id, instructor_id),
            )
            current_structure = cursor.fetchone()

        if not current_structure:
            logger.warning(
                f"Structure {structure_id} not found for instructor {instructor_id}"
            )
            return jsonify({"error": "structure_not_found_or_unauthorized"}), 404

        # Save to history before updating
        try:
            with get_db_connection().cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO grade_structure_history
                        (structure_id, structure_json, version, changed_by, changed_at)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        structure_id,
                        current_structure["structure_json"],
                        current_structure["version"],
                        instructor_id,
                        now,
                    ),
                )

                # Update existing structure with new version
                new_version = current_structure["version"] + 1
                cursor.execute(
                    """
                    UPDATE grade_structures
                    SET class_id = %s, structure_name = %s, structure_json = %s,
                        updated_at = %s, version = %s
                    WHERE id = %s AND created_by = %s
                    """,
                    (
                        class_id,
                        structure_name,
                        structure_json_str,
                        now,
                        new_version,
                        structure_id,
                        instructor_id,
                    ),
                )
                if cursor.rowcount == 0:
                    return (
                        jsonify({"error": "structure_not_found_or_unauthorized"}),
                        404,
                    )

            get_db_connection().commit()
            logger.info(
                f"Instructor {session.get('school_id')} updated grade structure {structure_id} to version {new_version}"
            )
            # Broadcast version update for this class
            try:
                emit_live_version_update(int(class_id))
            except Exception as _e:
                logger.warning(f"Emit after update structure failed: {str(_e)}")
            return (
                jsonify(
                    {
                        "success": True,
                        "message": f"Structure updated to version {new_version}",
                    }
                ),
                200,
            )

        except Exception as e:
            get_db_connection().rollback()
            logger.error(
                f"Failed to update grade structure {structure_id} for instructor {session.get('school_id')}: {str(e)}"
            )
            return (
                jsonify({"success": False, "error": "Failed to update structure"}),
                500,
            )
    else:
        # Insert new structure
        try:
            with get_db_connection().cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO grade_structures
                        (class_id, structure_name, structure_json, created_by, created_at, updated_at, is_active, version)
                    VALUES (%s, %s, %s, %s, %s, %s, 1, 1)
                    """,
                    (
                        class_id,
                        structure_name,
                        structure_json_str,
                        instructor_id,
                        now,
                        now,
                    ),
                )

            get_db_connection().commit()
            logger.info(
                f"Instructor {session.get('school_id')} created new grade structure for class {class_id}"
            )
            # Broadcast version update for this class
            try:
                emit_live_version_update(int(class_id))
            except Exception as _e:
                logger.warning(f"Emit after create structure failed: {str(_e)}")
            return (
                jsonify({"success": True, "message": "Structure saved successfully"}),
                201,
            )

        except Exception as e:
            get_db_connection().rollback()
            logger.error(
                f"Failed to create grade structure for instructor {session.get('school_id')}: {str(e)}"
            )
            return jsonify({"success": False, "error": "Failed to save structure"}), 500


from flask import render_template


@app.route("/test-grade-normalizer/<class_id>")
def test_grade_normalizer(class_id):
    try:
        # Get the active grade structure for this class
        with get_db_connection().cursor() as cursor:
            cursor.execute(
                """
                SELECT gs.*, c.course, c.track, c.section, c.class_type
                FROM grade_structures gs
                JOIN classes c ON gs.class_id = c.id
                WHERE gs.class_id = %s AND gs.is_active = 1
                """,
                (class_id,),
            )
            grade_structure = cursor.fetchone()

            if not grade_structure:
                flash("No active grading structure found for this class.", "error")
                return redirect(url_for("instructor_dashboard"))

            # Parse the structure JSON - it's already in the format we need
            structure = json.loads(grade_structure["structure_json"])

            # Get enrolled students
            cursor.execute(
                """
                SELECT 
                    sc.*, 
                    s.id as student_id,
                    s.course as student_course,
                    s.year_level,
                    s.section as student_section,
                    u.school_id,
                    pi.first_name,
                    pi.last_name,
                    pi.middle_name
                FROM student_classes sc
                JOIN students s ON sc.student_id = s.id
                JOIN users u ON s.user_id = u.id
                LEFT JOIN personal_info pi ON s.personal_info_id = pi.id
                WHERE sc.class_id = %s
                ORDER BY pi.last_name, pi.first_name
                """,
                (class_id,),
            )
            enrollments = cursor.fetchall()

            # Format student data
            students = []
            for enrollment in enrollments:
                first_name = enrollment.get("first_name") or ""
                middle_name = enrollment.get("middle_name") or ""
                last_name = enrollment.get("last_name") or ""
                school_id = enrollment.get("school_id") or ""

                if first_name and last_name:
                    student_name = (
                        f"{last_name}, {first_name} {middle_name}".strip()
                        if middle_name
                        else f"{last_name}, {first_name}"
                    )
                else:
                    student_name = (
                        school_id or f"Student {enrollment.get('student_id')}"
                    )

                # Get student scores if any exist
                cursor.execute(
                    """
                    SELECT ss.*, ga.name as assessment_name 
                    FROM student_scores ss
                    JOIN grade_assessments ga ON ss.assessment_id = ga.id
                    WHERE ss.student_id = %s
                    """,
                    (enrollment.get("student_id"),),
                )
                scores = {
                    score["assessment_name"]: score["score"]
                    for score in cursor.fetchall()
                }

                students.append(
                    {
                        "id": enrollment.get("student_id"),
                        "name": student_name,
                        "school_id": school_id,
                        "scores": scores,
                    }
                )

            # Debug print to verify structure
            print("Structure being passed to template:", structure)

            return render_template(
                "test_grade_normalizer.html",
                structure=structure,
                students=students,
                class_id=class_id,
            )

    except Exception as e:
        import traceback

        logger.error(
            f"Error in test_grade_normalizer: {str(e)}\n{traceback.format_exc()}"
        )
        return f"<pre style='color:red;'>{traceback.format_exc()}</pre>"


def normalize_structure(structure: dict):
    """Flatten structure_json into a list of row dicts.

    Expected input shape:
    {
      "LABORATORY": [{"name": str, "weight": num, "assessments": [{"name": str, "max_score": num}]}],
      "LECTURE":    [{...}]
    }
    Returns list of dicts: {category, name, weight, assessment, max_score}
    """
    rows = []
    if not isinstance(structure, dict):
        return rows

    for category_key in ["LABORATORY", "LECTURE"]:
        categories = structure.get(category_key, []) or []
        if not isinstance(categories, list):
            continue
        for cat in categories:
            if not isinstance(cat, dict):
                continue
            name = cat.get("name") or ""
            weight = cat.get("weight") or 0
            assessments = cat.get("assessments", []) or []
            if not isinstance(assessments, list):
                continue
            for a in assessments:
                if not isinstance(a, dict):
                    continue
                rows.append(
                    {
                        "category": category_key,
                        "name": name,
                        "weight": weight,
                        "assessment": a.get("name") or "",
                        "max_score": a.get("max_score") or 0,
                    }
                )
    return rows


def _instructor_owns_class(class_id: int, user_id: int) -> bool:
    """Check if the logged-in instructor owns the class."""
    try:
        with get_db_connection().cursor() as cursor:
            cursor.execute("SELECT id FROM instructors WHERE user_id = %s", (user_id,))
            instr = cursor.fetchone()
            if not instr:
                return False
            cursor.execute(
                "SELECT id FROM classes WHERE id = %s AND instructor_id = %s",
                (class_id, instr["id"]),
            )
            return cursor.fetchone() is not None
    except Exception:
        return False


def group_structure(normalized_rows: list):
    """Split normalized rows into strings vs numbers collections.

    Input row shape: {category, name, weight, assessment, max_score}
    Output: { strings: [{category, name, assessment}, ...], numbers: [{weight, max_score}, ...] }
    """
    strings = []
    numbers = []
    if not isinstance(normalized_rows, list):
        return {"strings": strings, "numbers": numbers}

    for row in normalized_rows:
        if not isinstance(row, dict):
            continue
        strings.append(
            {
                "category": row.get("category"),
                "name": row.get("name"),
                "assessment": row.get("assessment"),
            }
        )
        numbers.append(
            {
                "weight": row.get("weight", 0),
                "max_score": row.get("max_score", 0),
            }
        )

    return {"strings": strings, "numbers": numbers}


def get_equivalent(final_grade: float) -> str:
    """Map numeric grade to equivalent string. Placeholder scale; adjust to institution policy."""
    if final_grade >= 96:
        return "1.00"
    if final_grade >= 93:
        return "1.25"
    if final_grade >= 90:
        return "1.50"
    if final_grade >= 87:
        return "1.75"
    if final_grade >= 84:
        return "2.00"
    if final_grade >= 81:
        return "2.25"
    if final_grade >= 78:
        return "2.50"
    if final_grade >= 75:
        return "2.75"
    return "5.00"


def perform_grade_computation(
    formula: dict, normalized_rows: list, student_scores_named: list[dict]
) -> list[dict]:
    """Compute per-student grades.

    Assumptions:
    - normalized_rows contain repeated 'weight' per group name; we sum unique group weights per (category, name)
    - If formula defines category parts with weights, we use the sum of those weights as the category's total weight.
      We scale the category contribution from structure weights to match the formula total weight. If structure weight is 0,
      we use category average percent * formula total weight.
    - student_scores_named carries {'student_id', 'assessment_name', 'score'}; we match by assessment_name to normalized rows.
    """
    # Build lookup: assessment_name -> (category, group_name, max_score, group_weight)
    assess_lookup = {}
    # Also compute per-category group weights and assessment sets
    from collections import defaultdict

    category_group_weights = defaultdict(float)  # (category, group_name) -> weight
    category_assessments = defaultdict(list)  # category -> list of assessment names

    for row in normalized_rows:
        aname = row.get("assessment")
        category = row.get("category")
        gname = row.get("name")
        weight = float(row.get("weight") or 0)
        max_score = float(row.get("max_score") or 0)
        if aname:
            assess_lookup[aname] = (category, gname, max_score, weight)
            if category:
                category_assessments[category].append(aname)
        if category and gname:
            # Sum unique group weight: last one wins if repeated; we'll just ensure it's set (weights should be same per group's assessments)
            category_group_weights[(category, gname)] = weight

    # Compute category total weight from structure
    category_weight_structure = defaultdict(float)
    for (category, gname), w in category_group_weights.items():
        category_weight_structure[category] += float(w or 0)

    # Compute category total weight from formula (sum of parts)
    category_weight_formula = {}
    if isinstance(formula, dict):
        for category, details in formula.items():
            if isinstance(details, dict):
                total_w = 0.0
                for part in details.values():
                    try:
                        total_w += float(part.get("weight", 0))
                    except Exception:
                        continue
                category_weight_formula[category] = total_w

    # Group scores per student
    by_student = defaultdict(list)
    for rec in student_scores_named:
        sid = rec.get("student_id")
        aname = rec.get("assessment_name")
        score = rec.get("score")
        if sid is None or aname is None:
            continue
        by_student[sid].append((aname, float(score or 0)))

    results = []
    for student_id, pairs in by_student.items():
        # category -> { group_name -> (sum_score, sum_max) }
        cat_group_totals = defaultdict(lambda: defaultdict(lambda: [0.0, 0.0]))
        for aname, score in pairs:
            if aname not in assess_lookup:
                # Unknown assessment (not in current structure); skip
                continue
            category, gname, max_score, gweight = assess_lookup[aname]
            if max_score and max_score > 0:
                cat_group_totals[category][gname][0] += float(score)
                cat_group_totals[category][gname][1] += float(max_score)

        total_grade = 0.0
        for category, groups in cat_group_totals.items():
            # Compute contribution by groups using structure group weights
            cat_contrib = 0.0
            for gname, (sum_score, sum_max) in groups.items():
                if sum_max <= 0:
                    continue
                avg_percent = sum_score / sum_max  # 0..1
                gweight = category_group_weights.get((category, gname), 0.0)
                cat_contrib += avg_percent * gweight

            # Scale category contribution if formula dictates a different total weight
            desired_w = category_weight_formula.get(category)
            struct_w = category_weight_structure.get(category) or 0.0
            if desired_w is not None:
                if struct_w > 0:
                    cat_contrib = cat_contrib * (desired_w / struct_w)
                else:
                    # No structure weights; fallback to averaging all assessments in the category
                    assessments = category_assessments.get(category, [])
                    if assessments:
                        sum_score = 0.0
                        sum_max = 0.0
                        for aname in assessments:
                            # find student's score for this assessment
                            for a2, sc2 in pairs:
                                if a2 == aname:
                                    _, _, mx, _ = assess_lookup.get(
                                        a2, (None, None, 0.0, 0.0)
                                    )
                                    sum_score += sc2
                                    sum_max += float(mx or 0)
                        if sum_max > 0:
                            cat_contrib = (sum_score / sum_max) * desired_w

            total_grade += cat_contrib

        final_grade = round(total_grade, 2)
        equivalent = get_equivalent(final_grade)
        results.append(
            {
                "student_id": student_id,
                "final_grade": final_grade,
                "equivalent": equivalent,
            }
        )

    # Include students with no scores yet (enrolled but missing in by_student)
    try:
        with get_db_connection().cursor() as cursor:
            cursor.execute(
                "SELECT sc.student_id FROM student_classes sc WHERE sc.class_id = %s",
                (
                    (
                        request.view_args.get("class_id")
                        if request and request.view_args
                        else None
                    ),
                ),
            )
            enrolled = [row["student_id"] for row in cursor.fetchall() or []]
    except Exception:
        enrolled = []
    existing_ids = {r["student_id"] for r in results}
    for sid in enrolled:
        if sid not in existing_ids:
            results.append(
                {"student_id": sid, "final_grade": 0.0, "equivalent": "5.00"}
            )

    return sorted(results, key=lambda r: r["student_id"])  # stable order


def validate_structure_json(structure: dict):
    """Validate grade_structures.structure_json shape and types.

    Rules:
    - Top-level: dict with keys 'LABORATORY' and 'LECTURE' (arrays)
    - Each category item: { name: str, weight: number, assessments: array }
    - Each assessment: { name: str, max_score: number }

    Returns: (is_valid: bool, errors: list[str])
    """
    errors = []

    if not isinstance(structure, dict):
        return False, ["structure_json must be an object"]

    for top_key in ("LABORATORY", "LECTURE"):
        if top_key not in structure:
            errors.append(f"Missing required key: {top_key}")
            continue
        items = structure.get(top_key)
        if not isinstance(items, list):
            errors.append(f"{top_key} must be an array")
            continue
        for i, cat in enumerate(items):
            path = f"{top_key}[{i}]"
            if not isinstance(cat, dict):
                errors.append(f"{path} must be an object")
                continue
            name = cat.get("name")
            if not isinstance(name, str) or not name.strip():
                errors.append(f"{path}.name must be a non-empty string")
            weight = cat.get("weight")
            if not isinstance(weight, (int, float)):
                errors.append(f"{path}.weight must be a number")
            assessments = cat.get("assessments")
            if assessments is None:
                errors.append(f"{path}.assessments is required and must be an array")
                continue
            if not isinstance(assessments, list):
                errors.append(f"{path}.assessments must be an array")
                continue
            for j, a in enumerate(assessments):
                apath = f"{path}.assessments[{j}]"
                if not isinstance(a, dict):
                    errors.append(f"{apath} must be an object")
                    continue
                aname = a.get("name")
                if not isinstance(aname, str) or not aname.strip():
                    errors.append(f"{apath}.name must be a non-empty string")
                max_score = a.get("max_score")
                if not isinstance(max_score, (int, float)):
                    errors.append(f"{apath}.max_score must be a number")

    return len(errors) == 0, errors


def emit_live_version_update(class_id: int):
    """Emit the latest live version for a class to its room."""
    try:
        version = get_cached_class_live_version(class_id)
        socketio.emit(
            "live_version",
            {"class_id": class_id, "version": version},
            room=f"class-{class_id}",
        )
    except Exception as e:
        logger.error(f"Failed to emit live version for class {class_id}: {str(e)}")


@socketio.on("connect")
def _on_connect():
    emit("connected", {"message": "connected"})


@socketio.on("disconnect")
def _on_disconnect():
    # No-op; could add logging if needed
    pass


@socketio.on("subscribe_live_version")
def _on_subscribe_live_version(data):
    try:
        class_id = int(data.get("class_id"))
    except Exception:
        emit("error", {"message": "invalid class_id"})
        return
    join_room(f"class-{class_id}")
    # Immediately send current version to the subscriber only
    version = get_cached_class_live_version(class_id)
    emit("live_version", {"class_id": class_id, "version": version})


@socketio.on("unsubscribe_live_version")
def _on_unsubscribe_live_version(data):
    try:
        class_id = int(data.get("class_id"))
    except Exception:
        return
    leave_room(f"class-{class_id}")


# Simple in-memory cache for normalized structures, keyed by class_id + live version
_NORMALIZED_CACHE = {}
_NORMALIZED_CACHE_MAX = 200  # basic cap to prevent unbounded growth


def _cache_put(key: str, value):
    from datetime import datetime as _dt

    # Evict oldest if at capacity
    if len(_NORMALIZED_CACHE) >= _NORMALIZED_CACHE_MAX:
        oldest_key = None
        oldest_ts = None
        for k, v in _NORMALIZED_CACHE.items():
            ts = v.get("ts")
            if oldest_ts is None or (ts and ts < oldest_ts):
                oldest_key = k
                oldest_ts = ts
        if oldest_key:
            _NORMALIZED_CACHE.pop(oldest_key, None)

    _NORMALIZED_CACHE[key] = {"data": value, "ts": _dt.now()}


def _cache_get(key: str):
    item = _NORMALIZED_CACHE.get(key)
    return item.get("data") if item else None


# Grouped cache
_GROUPED_CACHE = {}
_GROUPED_CACHE_MAX = 200


def _grouped_cache_put(key: str, value):
    from datetime import datetime as _dt

    if len(_GROUPED_CACHE) >= _GROUPED_CACHE_MAX:
        oldest_key = None
        oldest_ts = None
        for k, v in _GROUPED_CACHE.items():
            ts = v.get("ts")
            if oldest_ts is None or (ts and ts < oldest_ts):
                oldest_key = k
                oldest_ts = ts
        if oldest_key:
            _GROUPED_CACHE.pop(oldest_key, None)

    _GROUPED_CACHE[key] = {"data": value, "ts": _dt.now()}


def _grouped_cache_get(key: str):
    item = _GROUPED_CACHE.get(key)
    return item.get("data") if item else None


def compute_class_live_version(class_id: int) -> str:
    """Compute the live version hash for a class, matching the API endpoint logic."""
    try:
        with get_db_connection().cursor() as cursor:
            cursor.execute(
                """
                SELECT COALESCE(MAX(updated_at), '1970-01-01 00:00:00') AS max_updated,
                       COALESCE(MAX(version), 0) AS max_version
                FROM grade_structures
                WHERE class_id = %s AND is_active = 1
                """,
                (class_id,),
            )
            gs = cursor.fetchone() or {}

            cursor.execute(
                """
                SELECT COALESCE(MAX(updated_at), '1970-01-01 00:00:00') AS class_updated
                FROM classes
                WHERE id = %s
                """,
                (class_id,),
            )
            cls = cursor.fetchone() or {}

            cursor.execute(
                """
                SELECT COUNT(*) AS cnt, COALESCE(MAX(joined_at), '1970-01-01 00:00:00') AS max_joined
                FROM student_classes
                WHERE class_id = %s
                """,
                (class_id,),
            )
            sc = cursor.fetchone() or {}

            cursor.execute(
                """
                SELECT COUNT(*) AS cnt, COALESCE(MAX(ss.updated_at), '1970-01-01 00:00:00') AS max_score_updated
                FROM student_scores ss
                WHERE ss.student_id IN (
                    SELECT sc2.student_id FROM student_classes sc2 WHERE sc2.class_id = %s
                )
                """,
                (class_id,),
            )
            ss = cursor.fetchone() or {}

            cursor.execute(
                """
                SELECT COALESCE(MAX(pi.updated_at), '1970-01-01 00:00:00') AS max_pi_updated
                FROM personal_info pi
                JOIN students s ON s.personal_info_id = pi.id
                JOIN student_classes sc3 ON sc3.student_id = s.id
                WHERE sc3.class_id = %s
                """,
                (class_id,),
            )
            pi = cursor.fetchone() or {}

        parts = [
            str(gs.get("max_updated")),
            str(gs.get("max_version")),
            str(cls.get("class_updated")),
            str(sc.get("cnt")),
            str(sc.get("max_joined")),
            str(ss.get("cnt")),
            str(ss.get("max_score_updated")),
            str(pi.get("max_pi_updated")),
        ]
        payload = "|".join(parts)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
    except Exception as e:
        logger.error(f"Failed to compute class live version for {class_id}: {str(e)}")
        return ""


# Micro-cache for live-version to reduce DB queries during frequent polling
_LIVE_VERSION_CACHE = {}
_LIVE_VERSION_TTL_SECONDS = 2.0


def get_cached_class_live_version(class_id: int) -> str:
    try:
        now_ts = datetime.now().timestamp()
        entry = _LIVE_VERSION_CACHE.get(class_id)
        if entry and (now_ts - entry.get("ts", 0)) < _LIVE_VERSION_TTL_SECONDS:
            return entry.get("version", "")

        version = compute_class_live_version(class_id)
        _LIVE_VERSION_CACHE[class_id] = {"version": version, "ts": now_ts}
        return version
    except Exception as e:
        logger.error(f"Live-version micro-cache error for class {class_id}: {str(e)}")
        return compute_class_live_version(class_id)


@app.route("/api/classes/<int:class_id>/normalized", methods=["GET"])
@login_required
def api_get_normalized(class_id: int):
    """Return flattened normalized structure for a class."""
    role = session.get("role")

    # Access control: instructors must own the class; admins allowed; students denied for now
    if role == "instructor":
        if not _instructor_owns_class(class_id, session.get("user_id")):
            return jsonify({"error": "access_denied"}), 403
    elif role == "admin":
        pass
    else:
        return jsonify({"error": "access_denied"}), 403

    try:
        # Use live version as cache key discriminator
        live_version = get_cached_class_live_version(class_id) or "noversion"
        cache_key = f"{class_id}:{live_version}"

        cached = _cache_get(cache_key)
        if cached is not None:
            return (
                jsonify({"class_id": class_id, "normalized": cached, "cached": True}),
                200,
            )

        with get_db_connection().cursor() as cursor:
            cursor.execute(
                """
                SELECT structure_json
                FROM grade_structures
                WHERE class_id = %s AND is_active = 1
                ORDER BY updated_at DESC
                LIMIT 1
                """,
                (class_id,),
            )
            row = cursor.fetchone()

        if not row:
            return jsonify({"error": "no_active_structure"}), 404

        structure = (
            json.loads(row["structure_json"]) if row.get("structure_json") else {}
        )
        normalized = normalize_structure(structure)
        _cache_put(cache_key, normalized)
        return (
            jsonify({"class_id": class_id, "normalized": normalized, "cached": False}),
            200,
        )
    except Exception as e:
        logger.error(f"Failed to normalize class {class_id}: {str(e)}")
        return jsonify({"error": "failed_to_normalize"}), 500


@app.route("/api/classes/<int:class_id>/grouped", methods=["GET"])
@login_required
def api_get_grouped(class_id: int):
    """Return grouped strings vs numbers for a class based on normalized structure."""
    role = session.get("role")

    # Access control mirrors normalized endpoint
    if role == "instructor":
        if not _instructor_owns_class(class_id, session.get("user_id")):
            return jsonify({"error": "access_denied"}), 403
    elif role == "admin":
        pass
    else:
        return jsonify({"error": "access_denied"}), 403

    try:
        live_version = get_cached_class_live_version(class_id) or "noversion"
        cache_key = f"{class_id}:{live_version}"

        cached = _grouped_cache_get(cache_key)
        if cached is not None:
            return (
                jsonify({"class_id": class_id, "grouped": cached, "cached": True}),
                200,
            )

        # Load active structure
        with get_db_connection().cursor() as cursor:
            cursor.execute(
                """
                SELECT structure_json
                FROM grade_structures
                WHERE class_id = %s AND is_active = 1
                ORDER BY updated_at DESC
                LIMIT 1
                """,
                (class_id,),
            )
            row = cursor.fetchone()

        if not row:
            return jsonify({"error": "no_active_structure"}), 404

        structure = (
            json.loads(row["structure_json"]) if row.get("structure_json") else {}
        )
        normalized = normalize_structure(structure)
        grouped = group_structure(normalized)
        _grouped_cache_put(cache_key, grouped)
        return jsonify({"class_id": class_id, "grouped": grouped, "cached": False}), 200
    except Exception as e:
        logger.error(f"Failed to group class {class_id}: {str(e)}")
        return jsonify({"error": "failed_to_group"}), 500


@app.route("/api/classes/<int:class_id>/calculate", methods=["GET"])
@login_required
def api_calculate_grades(class_id: int):
    """Perform grade computation using active formula (professor override or default)."""
    role = session.get("role")

    # Access control: instructors must own; admins allowed; students denied for now (Phase 7 will open)
    if role == "instructor":
        if not _instructor_owns_class(class_id, session.get("user_id")):
            return jsonify({"error": "access_denied"}), 403
    elif role == "admin":
        pass
    else:
        return jsonify({"error": "access_denied"}), 403

    try:
        # Load structure and build normalized rows
        structure = _load_active_structure(class_id)
        if not structure:
            return jsonify({"error": "no_active_structure"}), 404

        normalized = normalize_structure(structure)

        # Resolve formula
        formula = _resolve_active_formula_for_class(class_id)

        # Load student scores with names
        student_scores = _load_student_scores_with_names_for_class(class_id)

        results = perform_grade_computation(formula, normalized, student_scores)
        return (
            jsonify(
                {
                    "class_id": class_id,
                    "results": results,
                    "used_formula": bool(formula),
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Failed to calculate grades for class {class_id}: {str(e)}")
        return jsonify({"error": "failed_to_calculate"}), 500


@app.route("/instructor/class/<int:class_id>/grades", methods=["GET"])
@login_required
def instructor_class_grades(class_id: int):
    """Official instructor page for grade entry/visualization (initial version).

    Currently reuses the test template while we stabilize the API/UI.
    """
    if session.get("role") != "instructor":
        session.clear()
        flash("Unauthorized access.", "error")
        return redirect(url_for("login"))

    if not _instructor_owns_class(class_id, session.get("user_id")):
        flash("You do not have access to this class.", "error")
        return redirect(url_for("instructor_dashboard"))

    # Reuse the existing data assembly from the test route
    try:
        with get_db_connection().cursor() as cursor:
            cursor.execute(
                """
                SELECT gs.*, c.course, c.track, c.section, c.class_type
                FROM grade_structures gs
                JOIN classes c ON gs.class_id = c.id
                WHERE gs.class_id = %s AND gs.is_active = 1
                """,
                (class_id,),
            )
            grade_structure = cursor.fetchone()

            if not grade_structure:
                flash("No active grading structure found for this class.", "error")
                return redirect(url_for("instructor_dashboard"))

            structure = (
                json.loads(grade_structure["structure_json"])
                if grade_structure.get("structure_json")
                else {}
            )

            cursor.execute(
                """
                SELECT 
                    sc.*, 
                    s.id as student_id,
                    s.course as student_course,
                    s.year_level,
                    s.section as student_section,
                    u.school_id,
                    pi.first_name,
                    pi.last_name,
                    pi.middle_name
                FROM student_classes sc
                JOIN students s ON sc.student_id = s.id
                JOIN users u ON s.user_id = u.id
                LEFT JOIN personal_info pi ON s.personal_info_id = pi.id
                WHERE sc.class_id = %s
                ORDER BY pi.last_name, pi.first_name
                """,
                (class_id,),
            )
            enrollments = cursor.fetchall()

            students = []
            for enrollment in enrollments:
                first_name = enrollment.get("first_name") or ""
                middle_name = enrollment.get("middle_name") or ""
                last_name = enrollment.get("last_name") or ""
                school_id = enrollment.get("school_id") or ""

                if first_name and last_name:
                    student_name = (
                        f"{last_name}, {first_name} {middle_name}".strip()
                        if middle_name
                        else f"{last_name}, {first_name}"
                    )
                else:
                    student_name = (
                        school_id or f"Student {enrollment.get('student_id')}"
                    )

                cursor.execute(
                    """
                    SELECT ss.*, ga.name as assessment_name 
                    FROM student_scores ss
                    JOIN grade_assessments ga ON ss.assessment_id = ga.id
                    WHERE ss.student_id = %s
                    """,
                    (enrollment.get("student_id"),),
                )
                scores = {
                    score["assessment_name"]: score["score"]
                    for score in cursor.fetchall()
                }

                students.append(
                    {
                        "id": enrollment.get("student_id"),
                        "name": student_name,
                        "school_id": school_id,
                        "scores": scores,
                    }
                )

            return render_template(
                "test_grade_normalizer.html",  # Temporary reuse of test template
                structure=structure,
                students=students,
                class_id=class_id,
            )
    except Exception as e:
        import traceback

        logger.error(
            f"Error in instructor_class_grades: {str(e)}\n{traceback.format_exc()}"
        )
        return f"<pre style='color:red;'>{traceback.format_exc()}</pre>"


@app.route("/api/classes/<int:class_id>/live-version", methods=["GET"])
@login_required
def get_class_live_version(class_id: int):
    """Return a version hash that changes whenever relevant class data changes."""
    try:
        version = get_cached_class_live_version(class_id)
        if not version:
            return jsonify({"error": "Failed to compute version"}), 500
        return jsonify({"version": version, "generated_at": datetime.now().isoformat()})
    except Exception as e:
        logger.error(f"Failed to compute live version for class {class_id}: {str(e)}")
        return jsonify({"error": "Failed to compute version"}), 500


if __name__ == "__main__":
    logger.info("Application startup initiated")
    socketio.run(app, debug=True)
