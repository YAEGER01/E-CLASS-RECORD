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
    try:
        with conn.cursor() as cursor:
            print(
                f"[DB] Checking if structure {structure_id} belongs to instructor {instructor_id}..."
            )
            cursor.execute(
                "SELECT id FROM grade_structures WHERE id = %s AND created_by = %s",
                (structure_id, instructor_id),
            )
            row = cursor.fetchone()

            if not row:
                print("[DB] Structure not found or instructor mismatch.")
                return jsonify({"error": "structure_not_found_or_unauthorized"}), 404

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

    if "LABORATORY" not in structure_json or "LECTURE" not in structure_json:
        return jsonify({"error": "structure_json_missing_required_keys"}), 400

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


if __name__ == "__main__":
    logger.info("Application startup initiated")
    app.run(debug=True)
