import os
import logging
from datetime import datetime, timedelta  # type :ignore
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
from werkzeug.utils import secure_filename
from models import (
    User,
    Student,
    Instructor,
    Class,
    StudentClass,
    PersonalInfo,
    generate_class_codes,
)
from db_conn import init_database_with_app, db_conn
from models import db
from functools import wraps


# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("app.log")],
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = 3600  # 1 hour
logger.info("Flask application initialized with session configuration")


@app.route("/")
def home():
    logger.info("Home page accessed")
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        school_id = request.form.get("schoolId", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "student")

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
        session["user_id"] = user.id
        session["school_id"] = user.school_id
        session["role"] = user.role
        session.permanent = True

        logger.info(f"User {school_id} logged in successfully")

        # Redirect based on role
        if user.role == "admin":
            flash(f"Welcome back, Admin {user.school_id}!", "success")
            return redirect(url_for("admin_dashboard"))
        elif user.role == "instructor":
            flash(f"Welcome back, Instructor {user.school_id}!", "success")
            return redirect(url_for("instructor_dashboard"))
        else:  # student
            flash(f"Welcome back, {user.school_id}!", "success")
            return redirect(url_for("student_dashboard"))

    # GET - Clear any existing flash messages when accessing login page
    role = request.args.get("role", "student")
    logger.info(f"Login page accessed with role: {role}")
    return render_template("login.html", role=role)


@app.route("/index")
def index():
    logger.info("Index page accessed")
    return render_template("index.html")


def _handle_admin_login_timeout():
    """Handle admin login timeout logic when failed attempts threshold is reached."""
    if session["admin_failed_attempts"] >= 4:
        # Progressive timeout: 30s base, +30s for each subsequent timeout
        timeout_duration = 30 + (session["admin_timeout_duration"] * 30)
        timeout_until = datetime.now() + timedelta(seconds=timeout_duration)
        # Store as naive datetime string for session compatibility
        session["admin_timeout_until"] = timeout_until.strftime("%Y-%m-%d %H:%M:%S")
        session["admin_timeout_duration"] += 1
        logger.warning(f"Admin login timeout set for {timeout_duration} seconds")
    else:
        # Reset timeout duration if under threshold
        session["admin_timeout_duration"] = 0


@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    # Initialize admin login attempt tracking if not exists
    if "admin_failed_attempts" not in session:
        session["admin_failed_attempts"] = 0
    if "admin_timeout_until" not in session:
        session["admin_timeout_until"] = None
    if "admin_timeout_duration" not in session:
        session["admin_timeout_duration"] = 0

    # Ensure timeout_until is a string or None (not datetime object)
    if isinstance(session.get("admin_timeout_until"), datetime):
        session["admin_timeout_until"] = session["admin_timeout_until"].isoformat()

    # Check if currently in timeout period
    current_time = datetime.now()
    timeout_until_str = session.get("admin_timeout_until")

    if (
        timeout_until_str
        and timeout_until_str != "None"
        and isinstance(timeout_until_str, str)
    ):
        # Parse the stored datetime string back to datetime for comparison
        try:
            # Parse the stored format: "YYYY-MM-DD HH:MM:SS"
            timeout_until = datetime.strptime(timeout_until_str, "%Y-%m-%d %H:%M:%S")
        except (ValueError, AttributeError):
            # If parsing fails, skip timeout check
            timeout_until = None

        if timeout_until and current_time < timeout_until:
            remaining_seconds = int((timeout_until - current_time).total_seconds())
            # Don't redirect, just render the page with timeout message
            # The frontend JavaScript will handle the countdown display
            flash(
                f"Too many failed login attempts. Please wait {remaining_seconds} seconds before trying again.",
                "error",
            )

    # Check for URL parameters for direct login
    url_username = request.args.get("username", "").strip()
    url_password = request.args.get("password", "")
    url_role = request.args.get("role", "admin")

    # If URL parameters are provided, try to authenticate directly
    if url_username and url_password:
        logger.info(f"Direct admin login attempt for school ID: {url_username}")

        # Find user
        user = User.query.filter_by(school_id=url_username).first()

        if user and user.check_password(url_password) and user.role == url_role:
            # Login successful
            session["user_id"] = user.id
            session["school_id"] = user.school_id
            session["role"] = user.role
            session.permanent = True

            logger.info(f"Direct admin login successful for {url_username}")
            return redirect(url_for("admin_dashboard"))
        else:
            logger.warning(f"Direct admin login failed for {url_username}")
            return render_template("adminlogin.html", error="Invalid credentials.")

    if request.method == "POST":
        school_id = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = "admin"

        logger.info(f"Admin login attempt for school ID: {school_id}")

        # Validate input
        if not school_id or not password:
            logger.warning("Admin login failed: Missing credentials")
            flash("Please enter both school ID and password.", "error")
            return redirect(url_for("admin_login"))

        # Find user
        user = User.query.filter_by(school_id=school_id).first()

        if not user:
            logger.warning(f"Admin login failed: User {school_id} not found")
            session["admin_failed_attempts"] += 1
            _handle_admin_login_timeout()
            flash("Invalid admin credentials.", "error")
            return redirect(url_for("admin_login"))

        # Check password
        if not user.check_password(password):
            logger.warning(f"Admin login failed: Invalid password for user {school_id}")
            session["admin_failed_attempts"] += 1
            _handle_admin_login_timeout()
            flash("Invalid admin credentials.", "error")
            return redirect(url_for("admin_login"))

        # Check role
        if user.role != role:
            logger.warning(f"Admin login failed: Role mismatch for user {school_id}")
            session["admin_failed_attempts"] += 1
            _handle_admin_login_timeout()
            flash("Invalid admin credentials.", "error")
            return redirect(url_for("admin_login"))

        # Login successful - reset timeout counters
        session["admin_failed_attempts"] = 0
        session["admin_timeout_until"] = None
        session["admin_timeout_duration"] = 0

        session["user_id"] = user.id
        session["school_id"] = user.school_id
        session["role"] = user.role
        session.permanent = True

        logger.info(f"Admin {school_id} logged in successfully")
        return redirect(url_for("admin_dashboard"))

    logger.info("Admin login page accessed")
    return render_template("adminlogin.html")


@app.route("/instructor-login", methods=["GET", "POST"])
def instructor_login():
    # Check for URL parameters for direct login
    url_username = request.args.get("username", "").strip()
    url_password = request.args.get("password", "")
    url_role = request.args.get("role", "instructor")

    # If URL parameters are provided, try to authenticate directly
    if url_username and url_password:
        logger.info(f"Direct instructor login attempt for school ID: {url_username}")

        # Find user
        user = User.query.filter_by(school_id=url_username).first()

        if user and user.check_password(url_password) and user.role == url_role:
            # Check if instructor is suspended
            instructor = Instructor.query.filter_by(user_id=user.id).first()
            if instructor and instructor.status == "suspended":
                logger.warning(
                    f"Direct instructor login failed: Account suspended for user {url_username}"
                )
                return render_template(
                    "instructorlogin.html",
                    error="Your instructor account has been suspended. Please contact an administrator.",
                )

            # Login successful
            session["user_id"] = user.id
            session["school_id"] = user.school_id
            session["role"] = user.role
            session.permanent = True

            logger.info(f"Direct instructor login successful for {url_username}")
            return redirect(url_for("instructor_dashboard"))
        else:
            logger.warning(f"Direct instructor login failed for {url_username}")
            return render_template("instructorlogin.html", error="Invalid credentials.")

    if request.method == "POST":
        school_id = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = "instructor"

        logger.info(f"Instructor login attempt for school ID: {school_id}")

        # Validate input
        if not school_id or not password:
            logger.warning("Instructor login failed: Missing credentials")
            flash("Please enter both school ID and password.", "error")
            return redirect(url_for("instructor_login"))

        # Find user
        user = User.query.filter_by(school_id=school_id).first()

        if not user:
            logger.warning(f"Instructor login failed: User {school_id} not found")
            flash("Invalid instructor credentials.", "error")
            return redirect(url_for("instructor_login"))

        # Check password
        if not user.check_password(password):
            logger.warning(
                f"Instructor login failed: Invalid password for user {school_id}"
            )
            flash("Invalid instructor credentials.", "error")
            return redirect(url_for("instructor_login"))

        # Check role
        if user.role != role:
            logger.warning(
                f"Instructor login failed: Role mismatch for user {school_id}"
            )
            flash("Invalid instructor credentials.", "error")
            return redirect(url_for("instructor_login"))

        # Check if instructor is suspended
        instructor = Instructor.query.filter_by(user_id=user.id).first()
        if instructor and instructor.status == "suspended":
            logger.warning(
                f"Instructor login failed: Account suspended for user {school_id}"
            )
            flash(
                "Your instructor account has been suspended. Please contact an administrator.",
                "error",
            )
            return redirect(url_for("instructor_login"))

        # Login successful
        session["user_id"] = user.id
        session["school_id"] = user.school_id
        session["role"] = user.role
        session.permanent = True

        logger.info(f"Instructor {school_id} logged in successfully")
        return redirect(url_for("instructor_dashboard"))

    logger.info("Instructor login page accessed")
    return render_template("instructorlogin.html")


# Instructor Class Management Routes
@app.route("/instructor/classes")
@login_required
def instructor_classes():
    """Display instructor's class management page."""
    if session.get("role") != "instructor":
        flash("Access denied. Instructor privileges required.", "error")
        return redirect(url_for("home"))

    user = db.session.get(User, session["user_id"])
    if not user:
        # Session contains invalid user ID (likely due to database reset)
        session.clear()
        flash("Session expired. Please log in again.", "error")
        return redirect(url_for("login"))

    instructor = Instructor.query.filter_by(user_id=user.id).first()

    if not instructor:
        flash("Instructor profile not found.", "error")
        return redirect(url_for("home"))

    # Check if instructor is suspended
    if instructor.status == "suspended":
        session.clear()
        flash(
            "Your instructor account has been suspended. Please contact an administrator.",
            "error",
        )
        return redirect(url_for("instructor_login"))

    logger.info(f"Instructor {user.school_id} accessed class management")
    return render_template("instructor_classes.html")


@app.route("/instructor/class/<int:class_id>")
@login_required
def class_details(class_id):
    """Display detailed class information with student masterlist and grading."""
    if session.get("role") != "instructor":
        flash("Access denied. Instructor privileges required.", "error")
        return redirect(url_for("home"))

    user = db.session.get(User, session["user_id"])
    if not user:
        session.clear()
        flash("Session expired. Please log in again.", "error")
        return redirect(url_for("login"))

    instructor = Instructor.query.filter_by(user_id=user.id).first()

    if not instructor:
        flash("Instructor profile not found.", "error")
        return redirect(url_for("home"))

    # Check if instructor is suspended
    if instructor.status == "suspended":
        session.clear()
        flash(
            "Your instructor account has been suspended. Please contact an administrator.",
            "error",
        )
        return redirect(url_for("instructor_login"))

    # Find the class and verify ownership
    class_obj = Class.query.filter_by(id=class_id, instructor_id=instructor.id).first()
    if not class_obj:
        flash("Class not found or access denied.", "error")
        return redirect(url_for("instructor_dashboard"))

    # Get all enrolled students
    enrollments = StudentClass.query.filter_by(class_id=class_id).all()
    students = []

    for enrollment in enrollments:
        student = enrollment.student
        if student and student.user:
            students.append(
                {
                    "id": student.id,
                    "school_id": student.user.school_id,
                    "student_name": student.user.school_id,
                    "course": student.course,
                    "track": student.track,
                    "year_level": student.year_level,
                    "section": student.section,
                    "joined_at": (
                        enrollment.joined_at.isoformat()
                        if enrollment.joined_at
                        else None
                    ),
                }
            )

    logger.info(
        f"Instructor {user.school_id} viewed class details for {class_obj.class_id}"
    )
    return render_template(
        "class.html",
        class_obj=class_obj,
        students=students,
        total_students=len(students),
        students_json=students,
    )


@app.route("/api/instructor/classes", methods=["GET"])
@login_required
def get_instructor_classes():
    """Get all classes for the logged-in instructor."""
    if session.get("role") != "instructor":
        return jsonify({"error": "Access denied"}), 403

    user = db.session.get(User, session["user_id"])
    instructor = Instructor.query.filter_by(user_id=user.id).first()

    if not instructor:
        return jsonify({"error": "Instructor profile not found"}), 404

    classes = Class.query.filter_by(instructor_id=instructor.id).all()
    classes_data = []

    for cls in classes:
        # Count members (students enrolled in this class)
        member_count = StudentClass.query.filter_by(class_id=cls.id).count()

        classes_data.append(
            {
                "id": cls.id,
                "year": cls.year,
                "semester": cls.semester,
                "course": cls.course,
                "track": cls.track,
                "section": cls.section,
                "schedule": cls.schedule,
                "class_id": cls.class_id,
                "class_code": cls.class_code,
                "join_code": cls.join_code,
                "member_count": member_count,
                "created_at": cls.created_at.isoformat() if cls.created_at else None,
                "updated_at": cls.updated_at.isoformat() if cls.updated_at else None,
            }
        )

    logger.info(
        f"Retrieved {len(classes_data)} classes for instructor {user.school_id}"
    )
    return jsonify({"classes": classes_data})


@app.route("/api/instructor/classes", methods=["POST"])
@login_required
def create_class():
    """Create a new class for the logged-in instructor."""
    if session.get("role") != "instructor":
        return jsonify({"error": "Access denied"}), 403

    user = User.query.get(session["user_id"])
    instructor = Instructor.query.filter_by(user_id=user.id).first()

    if not instructor:
        return jsonify({"error": "Instructor profile not found"}), 404

    data = request.get_json()

    # Validate required fields
    required_fields = ["year", "semester", "course", "track", "section", "schedule"]
    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    # Validate section format (should be like "1A", "2B", etc.)
    section = data["section"]
    if not (len(section) == 2 and section[0].isdigit() and section[1].isalpha()):
        return (
            jsonify({"error": 'Section must be in format like "1A", "2B", etc.'}),
            400,
        )

    try:
        # Generate unique class codes
        class_code, join_code = generate_class_codes()

        # Ensure join_code is unique (very unlikely to collide, but just in case)
        while Class.query.filter_by(join_code=join_code).first():
            class_code, join_code = generate_class_codes()

        new_class = Class(
            instructor_id=instructor.id,
            year=data["year"],
            semester=data["semester"],
            course=data["course"],
            track=data["track"],
            section=section,
            schedule=data["schedule"],
            class_code=class_code,
            join_code=join_code,
        )

        db.session.add(new_class)
        db.session.commit()

        logger.info(f"Instructor {user.school_id} created class: {new_class.class_id}")
        return jsonify(
            {
                "success": True,
                "message": "Class created successfully",
                "class": {
                    "id": new_class.id,
                    "year": new_class.year,
                    "semester": new_class.semester,
                    "course": new_class.course,
                    "track": new_class.track,
                    "section": new_class.section,
                    "schedule": new_class.schedule,
                    "class_id": new_class.class_id,
                    "class_code": new_class.class_code,
                    "join_code": new_class.join_code,
                },
            }
        )

    except Exception as e:
        db.session.rollback()
        logger.error(
            f"Failed to create class for instructor {user.school_id}: {str(e)}"
        )
        return jsonify({"error": "Failed to create class"}), 500


@app.route("/api/instructor/classes/<int:class_id>", methods=["PUT"])
@login_required
def update_class(class_id):
    """Update an existing class."""
    if session.get("role") != "instructor":
        return jsonify({"error": "Access denied"}), 403

    user = db.session.get(User, session["user_id"])
    if not user:
        return jsonify({"error": "User not found"}), 401

    instructor = Instructor.query.filter_by(user_id=user.id).first()

    if not instructor:
        return jsonify({"error": "Instructor profile not found"}), 404

    # Find the class and verify ownership
    class_obj = Class.query.filter_by(id=class_id, instructor_id=instructor.id).first()
    if not class_obj:
        return jsonify({"error": "Class not found or access denied"}), 404

    data = request.get_json()

    # Validate required fields
    required_fields = ["year", "semester", "course", "track", "section", "schedule"]
    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    # Validate section format
    section = data["section"]
    if not (len(section) == 2 and section[0].isdigit() and section[1].isalpha()):
        return (
            jsonify({"error": 'Section must be in format like "1A", "2B", etc.'}),
            400,
        )

    try:
        class_obj.year = data["year"]
        class_obj.semester = data["semester"]
        class_obj.course = data["course"]
        class_obj.track = data["track"]
        class_obj.section = section
        class_obj.schedule = data["schedule"]

        db.session.commit()

        logger.info(
            f"Instructor {user.school_id} updated class {class_id}: {class_obj.class_id}"
        )
        return jsonify(
            {
                "success": True,
                "message": "Class updated successfully",
                "class": {
                    "id": class_obj.id,
                    "year": class_obj.year,
                    "semester": class_obj.semester,
                    "course": class_obj.course,
                    "track": class_obj.track,
                    "section": class_obj.section,
                    "schedule": class_obj.schedule,
                    "class_id": class_obj.class_id,
                    "class_code": class_obj.class_code,
                    "join_code": class_obj.join_code,
                },
            }
        )

    except Exception as e:
        db.session.rollback()
        logger.error(
            f"Failed to update class {class_id} for instructor {user.school_id}: {str(e)}"
        )
        return jsonify({"error": "Failed to update class"}), 500


@app.route("/api/instructor/classes/<int:class_id>", methods=["DELETE"])
@login_required
def delete_class(class_id):
    """Delete a class."""
    if session.get("role") != "instructor":
        return jsonify({"error": "Access denied"}), 403

    user = db.session.get(User, session["user_id"])
    if not user:
        return jsonify({"error": "User not found"}), 401

    instructor = Instructor.query.filter_by(user_id=user.id).first()

    if not instructor:
        return jsonify({"error": "Instructor profile not found"}), 404

    # Find the class and verify ownership
    class_obj = Class.query.filter_by(id=class_id, instructor_id=instructor.id).first()
    if not class_obj:
        return jsonify({"error": "Class not found or access denied"}), 404

    try:
        class_id_display = class_obj.class_id
        db.session.delete(class_obj)
        db.session.commit()

        logger.info(f"Instructor {user.school_id} deleted class: {class_id_display}")
        return jsonify({"success": True, "message": "Class deleted successfully"})

    except Exception as e:
        db.session.rollback()
        logger.error(
            f"Failed to delete class {class_id} for instructor {user.school_id}: {str(e)}"
        )
        return jsonify({"error": "Failed to delete class"}), 500


@app.route("/api/instructor/classes/<int:class_id>/members", methods=["GET"])
@login_required
def get_class_members(class_id):
    """Get all members (students) of a specific class."""
    if session.get("role") != "instructor":
        return jsonify({"error": "Access denied"}), 403

    user = db.session.get(User, session["user_id"])
    if not user:
        return jsonify({"error": "User not found"}), 401

    instructor = Instructor.query.filter_by(user_id=user.id).first()

    if not instructor:
        return jsonify({"error": "Instructor profile not found"}), 404

    # Find the class and verify ownership
    class_obj = Class.query.filter_by(id=class_id, instructor_id=instructor.id).first()
    if not class_obj:
        return jsonify({"error": "Class not found or access denied"}), 404

    try:
        # Get all student enrollments for this class
        enrollments = StudentClass.query.filter_by(class_id=class_id).all()

        members = []
        for enrollment in enrollments:
            student = enrollment.student
            if student and student.user:
                members.append(
                    {
                        "id": student.id,
                        "school_id": student.user.school_id,
                        "student_name": (
                            student.personal_info.full_name
                            if student.personal_info
                            else f"{student.user.school_id}"
                        ),
                        "course": student.course,
                        "year_level": student.year_level,
                        "section": student.section,
                        "joined_at": (
                            enrollment.joined_at.isoformat()
                            if enrollment.joined_at
                            else None
                        ),
                    }
                )

        logger.info(
            f"Instructor {user.school_id} viewed {len(members)} members of class {class_obj.class_id}"
        )
        return jsonify(
            {
                "class_id": class_obj.class_id,
                "class_name": f"{class_obj.course} {class_obj.section}",
                "members": members,
                "total_members": len(members),
            }
        )

    except Exception as e:
        logger.error(f"Failed to get members for class {class_id}: {str(e)}")
        return jsonify({"error": "Failed to get class members"}), 500


# Student Class Management Routes
@app.route("/api/student/join-class", methods=["POST"])
@login_required
def join_class():
    """Join a class using join code."""
    if session.get("role") != "student":
        return jsonify({"error": "Access denied. Student privileges required."}), 403

    user = User.query.get(session["user_id"])
    if not user:
        return jsonify({"error": "User not found"}), 401

    student = Student.query.filter_by(user_id=user.id).first()
    if not student:
        return jsonify({"error": "Student profile not found"}), 404

    data = request.get_json()
    join_code = data.get("join_code", "").strip().upper()

    if not join_code:
        return jsonify({"error": "Join code is required"}), 400

    # Find class by join code
    class_obj = Class.query.filter_by(join_code=join_code).first()
    if not class_obj:
        return jsonify({"error": "Invalid join code. Class not found."}), 404

    # Check if student is already enrolled
    existing_enrollment = StudentClass.query.filter_by(
        student_id=student.id, class_id=class_obj.id
    ).first()

    if existing_enrollment:
        return jsonify({"error": "You are already enrolled in this class"}), 400

    try:
        # Create enrollment
        enrollment = StudentClass(student_id=student.id, class_id=class_obj.id)
        db.session.add(enrollment)
        db.session.commit()

        logger.info(f"Student {user.school_id} joined class: {class_obj.class_id}")
        return jsonify(
            {
                "success": True,
                "message": f"Successfully joined class: {class_obj.class_id}",
                "class": {
                    "id": class_obj.id,
                    "class_id": class_obj.class_id,
                    "course": class_obj.course,
                    "section": class_obj.section,
                    "schedule": class_obj.schedule,
                },
            }
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to join class for student {user.school_id}: {str(e)}")
        return jsonify({"error": "Failed to join class"}), 500


@app.route("/api/student/joined-classes", methods=["GET"])
@login_required
def get_joined_classes():
    """Get all classes joined by the logged-in student."""
    if session.get("role") != "student":
        return jsonify({"error": "Access denied. Student privileges required."}), 403

    user = User.query.get(session["user_id"])
    if not user:
        return jsonify({"error": "User not found"}), 401

    student = Student.query.filter_by(user_id=user.id).first()
    if not student:
        return jsonify({"error": "Student profile not found"}), 404

    # Get all enrollments for this student with joined instructor and user data
    enrollments = StudentClass.query.filter_by(student_id=student.id).all()
    classes_data = []

    for enrollment in enrollments:
        class_obj = enrollment.class_obj
        instructor_name = "Unknown"
        if class_obj.instructor:
            # Get the instructor's user information
            instructor_user = User.query.get(class_obj.instructor.user_id)
            if instructor_user:
                instructor_name = instructor_user.school_id

        classes_data.append(
            {
                "id": class_obj.id,
                "class_id": class_obj.class_id,
                "year": class_obj.year,
                "semester": class_obj.semester,
                "course": class_obj.course,
                "track": class_obj.track,
                "section": class_obj.section,
                "schedule": class_obj.schedule,
                "class_code": class_obj.class_code,
                "join_code": class_obj.join_code,
                "instructor_name": instructor_name,
                "joined_at": (
                    enrollment.joined_at.isoformat() if enrollment.joined_at else None
                ),
            }
        )

    logger.info(
        f"Retrieved {len(classes_data)} joined classes for student {user.school_id}"
    )
    return jsonify({"classes": classes_data})


@app.route("/student-login", methods=["GET", "POST"])
def student_login():
    # Check for URL parameters for direct login
    url_username = request.args.get("username", "").strip()
    url_password = request.args.get("password", "")
    url_role = request.args.get("role", "student")

    # If URL parameters are provided, try to authenticate directly
    if url_username and url_password:
        logger.info(f"Direct login attempt for school ID: {url_username}")

        # Find user
        user = User.query.filter_by(school_id=url_username).first()

        if user and user.check_password(url_password) and user.role == url_role:
            # Login successful
            session["user_id"] = user.id
            session["school_id"] = user.school_id
            session["role"] = user.role
            session.permanent = True

            logger.info(f"Direct login successful for {url_username}")
            return redirect(url_for("student_dashboard"))
        else:
            logger.warning(f"Direct login failed for {url_username}")
            return render_template("studentlogin.html", error="Invalid credentials.")

    if request.method == "POST":
        school_id = request.form.get(
            "username", ""
        ).strip()  # Form uses 'username' field
        password = request.form.get("password", "")
        role = "student"  # This is the student login page

        logger.info(f"Student login attempt for school ID: {school_id}")

        # Validate input
        if not school_id or not password:
            logger.warning("Student login failed: Missing credentials")
            flash("Please enter both school ID and password.", "error")
            return redirect(url_for("student_login"))

        # Find user
        user = User.query.filter_by(school_id=school_id).first()

        if not user:
            logger.warning(f"Student login failed: User {school_id} not found")
            flash("Invalid student credentials.", "error")
            return redirect(url_for("student_login"))

        # Check password
        if not user.check_password(password):
            logger.warning(
                f"Student login failed: Invalid password for user {school_id}"
            )
            flash("Invalid student credentials.", "error")
            return redirect(url_for("student_login"))

        # Check role
        if user.role != role:
            logger.warning(f"Student login failed: Role mismatch for user {school_id}")
            flash("Invalid student credentials.", "error")
            return redirect(url_for("student_login"))

        # Login successful
        session["user_id"] = user.id
        session["school_id"] = user.school_id
        session["role"] = user.role
        session.permanent = True

        logger.info(f"Student {school_id} logged in successfully")
        return redirect(url_for("student_dashboard"))

    logger.info("Student login page accessed")
    return render_template("studentlogin.html")


@app.route("/about")
def about():
    logger.info("About page accessed")
    return render_template("about.html")


@app.route("/logout")
def logout():
    user_id = session.get("user_id")
    school_id = session.get("school_id")
    session.clear()
    logger.info(f"User {school_id} (ID: {user_id}) logged out")
    # Don't flash logout message to avoid confusion during next login
    return redirect(url_for("home"))


@app.route("/student-dashboard")
def student_dashboard():
    if "user_id" not in session:
        flash("Please log in to access this page.", "warning")
        return redirect(url_for("login"))

    user = db.session.get(User, session["user_id"])
    if not user or user.role != "student":
        session.clear()
        flash("Unauthorized access.", "error")
        return redirect(url_for("login"))

    logger.info(f"Student dashboard accessed by {user.school_id}")
    return render_template("student_dashboard.html", user=user)


@app.route("/instructor-dashboard")
def instructor_dashboard():
    if "user_id" not in session:
        flash("Please log in to access this page.", "warning")
        return redirect(url_for("login"))

    user = db.session.get(User, session["user_id"])
    if not user or user.role != "instructor":
        session.clear()
        flash("Unauthorized access.", "error")
        return redirect(url_for("login"))

    # Check if instructor is suspended
    instructor = Instructor.query.filter_by(user_id=user.id).first()
    if instructor and instructor.status == "suspended":
        session.clear()
        flash(
            "Your instructor account has been suspended. Please contact an administrator.",
            "error",
        )
        return redirect(url_for("instructor_login"))

    logger.info(f"Instructor dashboard accessed by {user.school_id}")
    return render_template("instructor_dashboard.html", user=user)


@app.route("/admin-dashboard")
def admin_dashboard():
    if "user_id" not in session:
        flash("Please log in to access this page.", "warning")
        return redirect(url_for("login"))

    user = db.session.get(User, session["user_id"])
    if not user or user.role != "admin":
        session.clear()
        flash("Unauthorized access.", "error")
        return redirect(url_for("login"))

    logger.info(f"Admin dashboard accessed by {user.school_id}")
    return render_template("admin_dashboard.html", user=user)


@app.route("/admin/create-instructor", methods=["POST"])
def create_instructor():
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Not authenticated"}), 401

    user = db.session.get(User, session["user_id"])
    if not user or user.role != "admin":
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
        existing_user = User.query.filter_by(school_id=school_id).first()
        if existing_user:
            errors.append("School ID already exists")

        # Check if email already exists
        existing_email = PersonalInfo.query.filter_by(email=email).first()
        if existing_email:
            errors.append("Email already exists")

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
        if not (
            any(c.isupper() for c in password) or any(c.islower() for c in password)
        ):
            errors.append(
                "Password must contain at least one letter (upper or lowercase)"
            )
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

        # Create personal information record
        personal_info = PersonalInfo(
            first_name=first_name,
            last_name=last_name,
            middle_name=middle_name if middle_name else None,
            email=email,
            phone=phone if phone else None,
            address=address if address else None,
            birth_date=(
                datetime.strptime(birth_date, "%Y-%m-%d").date() if birth_date else None
            ),
            gender=gender if gender else None,
            emergency_contact_name=(
                emergency_contact_name if emergency_contact_name else None
            ),
            emergency_contact_phone=(
                emergency_contact_phone if emergency_contact_phone else None
            ),
        )

        # Create instructor user
        new_instructor = User(school_id=school_id, role="instructor")
        new_instructor.set_password(password)

        # Create instructor profile
        instructor_profile = Instructor(
            department=department,
            specialization=specialization if specialization else None,
            employee_id=employee_id if employee_id else None,
        )

        # Save to database
        db.session.add(personal_info)
        db.session.flush()  # Get personal_info ID

        db.session.add(new_instructor)
        db.session.flush()  # Get user ID

        instructor_profile.user_id = new_instructor.id
        instructor_profile.personal_info_id = personal_info.id
        db.session.add(instructor_profile)
        db.session.commit()

        logger.info(
            f"Instructor created successfully: {first_name} {last_name} ({school_id}) by admin {user.school_id}"
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
        db.session.rollback()
        logger.error(f"Instructor creation failed: {str(e)}")
        return (
            jsonify(
                {"success": False, "message": "Failed to create instructor account"}
            ),
            500,
        )


# Instructor Management API Endpoints
@app.route("/api/admin/instructors", methods=["GET"])
@login_required
def get_instructors():
    """Get all instructors with analytics data."""
    if session.get("role") != "admin":
        return jsonify({"error": "Access denied. Admin privileges required."}), 403

    try:
        # Get all instructors with their related data - handle missing columns gracefully
        try:
            instructors = (
                db.session.query(Instructor).join(User).outerjoin(PersonalInfo).all()
            )
        except Exception as e:
            if "Unknown column" in str(e):
                # Fallback for missing columns - use basic query
                instructors = Instructor.query.all()
                # Set default values for missing columns
                for instructor in instructors:
                    if not hasattr(instructor, "status") or instructor.status is None:
                        instructor.status = "active"
                    if (
                        not hasattr(instructor, "updated_at")
                        or instructor.updated_at is None
                    ):
                        instructor.updated_at = instructor.created_at
            else:
                raise e

        instructors_data = []
        active_count = 0
        suspended_count = 0

        for instructor in instructors:
            # Handle missing personal_info relationship
            if (
                not hasattr(instructor, "personal_info")
                or instructor.personal_info is None
            ):
                instructor.personal_info = None

            # Get user information for this instructor
            instructor_user = User.query.filter_by(id=instructor.user_id).first()

            instructor_data = {
                "id": instructor.id,
                "school_id": (
                    instructor_user.school_id if instructor_user else "Unknown"
                ),
                "name": getattr(instructor, "full_name", f"Instructor {instructor.id}"),
                "email": (
                    instructor.personal_info.email
                    if instructor.personal_info
                    else "N/A"
                ),
                "department": instructor.department or "Not specified",
                "specialization": instructor.specialization or "Not specified",
                "employee_id": instructor.employee_id or "Not specified",
                "status": getattr(instructor, "status", "active"),
                "hire_date": (
                    instructor.hire_date.isoformat() if instructor.hire_date else None
                ),
                "created_at": (
                    instructor.created_at.isoformat() if instructor.created_at else None
                ),
                "class_count": len(getattr(instructor, "classes", [])),
            }

            if getattr(instructor, "status", "active") == "active":
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
        try:
            instructor = Instructor.query.filter_by(id=instructor_id).first()
        except Exception as e:
            if "Unknown column" in str(e):
                # Fallback for missing columns
                instructor = Instructor.query.filter_by(id=instructor_id).first()
                if instructor:
                    # Set default values for missing columns
                    if not hasattr(instructor, "status") or instructor.status is None:
                        instructor.status = "active"
                    if (
                        not hasattr(instructor, "updated_at")
                        or instructor.updated_at is None
                    ):
                        instructor.updated_at = instructor.created_at
            else:
                raise e

        if not instructor:
            return jsonify({"error": "Instructor not found"}), 404

        # Get user information separately to handle missing relationships
        user = User.query.filter_by(id=instructor.user_id).first()

        instructor_details = {
            "id": instructor.id,
            "school_id": user.school_id if user else "Unknown",
            "personal_info": {
                "first_name": (
                    instructor.personal_info.first_name
                    if instructor.personal_info
                    else "N/A"
                ),
                "last_name": (
                    instructor.personal_info.last_name
                    if instructor.personal_info
                    else "N/A"
                ),
                "middle_name": (
                    instructor.personal_info.middle_name
                    if instructor.personal_info
                    else None
                ),
                "email": (
                    instructor.personal_info.email
                    if instructor.personal_info
                    else "N/A"
                ),
                "phone": (
                    instructor.personal_info.phone if instructor.personal_info else None
                ),
                "address": (
                    instructor.personal_info.address
                    if instructor.personal_info
                    else None
                ),
                "birth_date": (
                    instructor.personal_info.birth_date.isoformat()
                    if instructor.personal_info and instructor.personal_info.birth_date
                    else None
                ),
                "gender": (
                    instructor.personal_info.gender
                    if instructor.personal_info
                    else None
                ),
                "emergency_contact_name": (
                    instructor.personal_info.emergency_contact_name
                    if instructor.personal_info
                    else None
                ),
                "emergency_contact_phone": (
                    instructor.personal_info.emergency_contact_phone
                    if instructor.personal_info
                    else None
                ),
            },
            "professional_info": {
                "department": instructor.department,
                "specialization": instructor.specialization,
                "employee_id": instructor.employee_id,
                "hire_date": (
                    instructor.hire_date.isoformat() if instructor.hire_date else None
                ),
            },
            "account_info": {
                "status": instructor.status,
                "created_at": (
                    instructor.created_at.isoformat() if instructor.created_at else None
                ),
                "updated_at": (
                    instructor.updated_at.isoformat() if instructor.updated_at else None
                ),
            },
            "statistics": {
                "total_classes": len(instructor.classes),
                "class_list": [
                    {
                        "id": cls.id,
                        "class_id": cls.class_id,
                        "course": cls.course,
                        "section": cls.section,
                        "year": cls.year,
                        "semester": cls.semester,
                    }
                    for cls in instructor.classes
                ],
            },
        }

        logger.info(
            f"Admin {session.get('school_id')} viewed instructor details: {instructor.school_id}"
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

        try:
            instructor = Instructor.query.filter_by(id=instructor_id).first()
            if not instructor:
                return jsonify({"error": "Instructor not found"}), 404

            old_status = getattr(instructor, "status", "active")
            instructor.status = new_status
            db.session.commit()
        except Exception as e:
            if "Unknown column" in str(e):
                # Handle missing status column
                return (
                    jsonify(
                        {
                            "error": "Database schema needs to be updated. Please run the migration script."
                        }
                    ),
                    500,
                )
            else:
                raise e

        logger.info(
            f"Admin {session.get('school_id')} changed instructor status from {old_status} to {new_status}"
        )
        return jsonify(
            {
                "success": True,
                "message": f"Instructor {new_status} successfully",
                "instructor": {
                    "id": instructor.id,
                    "school_id": (
                        User.query.filter_by(id=instructor.user_id).first().school_id
                        if User.query.filter_by(id=instructor.user_id).first()
                        else "Unknown"
                    ),
                    "name": instructor.full_name,
                    "status": instructor.status,
                },
            }
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to update instructor status: {str(e)}")
        return jsonify({"error": "Failed to update instructor status"}), 500


@app.route("/api/admin/instructors/<int:instructor_id>", methods=["DELETE"])
@login_required
def delete_instructor(instructor_id):
    """Delete an instructor account and all associated data."""
    if session.get("role") != "admin":
        return jsonify({"error": "Access denied. Admin privileges required."}), 403

    try:
        instructor = Instructor.query.filter_by(id=instructor_id).first()
        if not instructor:
            return jsonify({"error": "Instructor not found"}), 404

        # Check if instructor has active classes
        active_classes = Class.query.filter_by(instructor_id=instructor.id).count()
        if active_classes > 0:
            return (
                jsonify(
                    {
                        "error": f"Cannot delete instructor with {active_classes} active classes. Please reassign or delete classes first."
                    }
                ),
                400,
            )

        instructor_name = instructor.full_name
        user = User.query.filter_by(id=instructor.user_id).first()
        school_id = user.school_id if user else "Unknown"

        # Get personal info for logging
        personal_info = instructor.personal_info

        # Delete related records in proper order to handle cascading deletes correctly
        try:
            # 1. Delete classes first (they reference the instructor)
            classes = Class.query.filter_by(instructor_id=instructor.id).all()
            for class_obj in classes:
                db.session.delete(class_obj)

            # 2. Delete instructor record (this should cascade to related grading templates and categories)
            db.session.delete(instructor)

            # 3. Delete user record (instructor profile references this)
            if user:
                db.session.delete(user)

            # 4. Delete personal info record (instructor profile references this)
            if personal_info:
                db.session.delete(personal_info)

            # Commit all deletions
            db.session.commit()

        except Exception as cascade_error:
            db.session.rollback()
            logger.error(f"Cascading delete failed: {str(cascade_error)}")
            # Fallback to manual deletion if cascading fails
            try:
                # Manual cleanup in case cascading doesn't work properly
                if personal_info:
                    db.session.delete(personal_info)
                if user:
                    db.session.delete(user)
                db.session.delete(instructor)
                db.session.commit()
            except Exception as manual_error:
                db.session.rollback()
                logger.error(f"Manual delete also failed: {str(manual_error)}")
                return (
                    jsonify({"error": "Failed to delete instructor and related data"}),
                    500,
                )

        logger.info(
            f"Admin {session.get('school_id')} deleted instructor: {school_id} ({instructor_name})"
        )
        return jsonify(
            {
                "success": True,
                "message": f"Instructor {instructor_name} deleted successfully",
            }
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to delete instructor: {str(e)}")
        return jsonify({"error": "Failed to delete instructor"}), 500


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        logger.info("Registration form submitted")

        # Get form data
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
                flash(error, "error")
            logger.warning(
                f"Registration validation failed for school ID {school_id}: {errors}"
            )
            # Repopulate form with previously entered data
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
            new_user = User(school_id=school_id, role="student")
            new_user.set_password(password)

            # Handle file uploads
            upload_dir = os.path.join(app.root_path, "static", "uploads")
            os.makedirs(upload_dir, exist_ok=True)

            id_front_path = None
            id_back_path = None
            face_photo_path = None

            if "idFront" in request.files:
                id_front_file = request.files["idFront"]
                if id_front_file and id_front_file.filename:
                    filename = secure_filename(
                        f"{school_id}_id_front_{id_front_file.filename}"
                    )
                    id_front_file.save(os.path.join(upload_dir, filename))
                    id_front_path = f"uploads/{filename}"

            if "idBack" in request.files:
                id_back_file = request.files["idBack"]
                if id_back_file and id_back_file.filename:
                    filename = secure_filename(
                        f"{school_id}_id_back_{id_back_file.filename}"
                    )
                    id_back_file.save(os.path.join(upload_dir, filename))
                    id_back_path = f"uploads/{filename}"

            if "facePhoto" in request.files:
                face_photo_file = request.files["facePhoto"]
                if face_photo_file and face_photo_file.filename:
                    filename = secure_filename(
                        f"{school_id}_face_{face_photo_file.filename}"
                    )
                    face_photo_file.save(os.path.join(upload_dir, filename))
                    face_photo_path = f"uploads/{filename}"

            # Create personal information record for student
            personal_info = PersonalInfo(
                first_name="Student",  # Default values since registration form doesn't collect personal info yet
                last_name="User",
                middle_name=None,
                email=f"{school_id}@student.edu",  # Placeholder email
                phone=None,
                address=None,
                birth_date=None,
                gender=None,
                emergency_contact_name=None,
                emergency_contact_phone=None,
            )

            # Create student profile
            student_profile = Student(
                course=course,
                track=track,
                year_level=int(year_level),
                section=section,
                id_front_path=id_front_path,
                id_back_path=id_back_path,
                face_photo_path=face_photo_path,
            )

            # Save to database
            db.session.add(personal_info)
            db.session.flush()  # Get personal_info ID

            db.session.add(new_user)
            db.session.flush()  # Get user ID

            student_profile.user_id = new_user.id
            student_profile.personal_info_id = personal_info.id
            db.session.add(student_profile)
            db.session.commit()

            logger.info(f"User registered successfully: {school_id}")
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("login"))

        except Exception as e:
            db.session.rollback()
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


# Initialize database on app startup
if __name__ == "__main__":
    logger.info("Application startup initiated")
    if init_database_with_app(app):
        logger.info("🚀 Starting Flask application...")
        app.run(debug=True)
    else:
        logger.error(
            "❌ Failed to initialize database. Please check your database configuration."
        )
        exit(1)
