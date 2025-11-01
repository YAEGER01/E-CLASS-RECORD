import logging
from datetime import datetime
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
)
from werkzeug.security import generate_password_hash, check_password_hash

from utils.db_conn import get_db_connection

logger = logging.getLogger(__name__)


# Blueprint: auth (no url_prefix to preserve original paths)
auth_bp = Blueprint("auth", __name__)


# Route: GET "/login"
# Used by: login.html (rendered by this route); many protected routes redirect here on auth failure
# Purpose: Role selection and entry point to admin/instructor/student login pages.
@auth_bp.route("/login", endpoint="login")
def login():
    """Display the role selection page (landing page with login options)"""
    logger.info("Login role selection page accessed")
    return render_template("login.html")


# Route: GET/POST "/admin-login"
# Used by: adminlogin.html (form posts here); redirects from protected admin pages when not authenticated
# Purpose: Authenticate admin users; sets session and redirects to /admin-dashboard.
@auth_bp.route("/admin-login", methods=["GET", "POST"], endpoint="admin_login")
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
            return redirect(url_for("auth.admin_login"))

        # Find user using raw SQL
        try:
            with get_db_connection().cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE school_id = %s", (school_id,))
                user = cursor.fetchone()
        except Exception as e:
            logger.error(f"Database error during admin user lookup: {str(e)}")
            flash("An error occurred. Please try again.", "error")
            return redirect(url_for("auth.admin_login"))

        if not user:
            logger.warning(f"Admin login failed: User {school_id} not found")
            session["admin_failed_attempts"] += 1
            flash("Invalid admin credentials.", "error")
            return redirect(url_for("auth.admin_login"))

        # Check password
        if not check_password_hash(user["password_hash"], password):
            logger.warning(f"Admin login failed: Invalid password for user {school_id}")
            session["admin_failed_attempts"] += 1
            flash("Invalid admin credentials.", "error")
            return redirect(url_for("auth.admin_login"))

        # Check role
        if user["role"] != role:
            logger.warning(f"Admin login failed: Role mismatch for user {school_id}")
            session["admin_failed_attempts"] += 1
            flash("Invalid admin credentials.", "error")
            return redirect(url_for("auth.admin_login"))

        # Login successful - reset timeout counters
        session["admin_failed_attempts"] = 0
        session["admin_timeout_until"] = None
        session["admin_timeout_duration"] = 0

        session["user_id"] = user["id"]
        session["school_id"] = user["school_id"]
        session["role"] = user["role"]
        session.permanent = True

        logger.info(f"Admin {school_id} logged in successfully")
        return redirect(url_for("dashboard.admin_dashboard"))

    logger.info("Admin login page accessed")
    return render_template("adminlogin.html")


# Route: GET/POST "/instructor-login"
# Used by: instructorlogin.html (form posts here); redirects from instructor-only pages when unauthenticated
# Purpose: Authenticate instructors; sets session and redirects to /instructor-dashboard.
@auth_bp.route(
    "/instructor-login", methods=["GET", "POST"], endpoint="instructor_login"
)
def instructor_login():
    if request.method == "POST":
        school_id = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = "instructor"

        logger.info(f"Instructor login attempt for school ID: {school_id}")

        if not school_id or not password:
            logger.warning("Instructor login failed: Missing credentials")
            flash("Please enter both school ID and password.", "error")
            return redirect(url_for("auth.instructor_login"))

        # Find user using raw SQL
        try:
            with get_db_connection().cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE school_id = %s", (school_id,))
                user = cursor.fetchone()
        except Exception as e:
            logger.error(f"Database error during instructor user lookup: {str(e)}")
            flash("An error occurred. Please try again.", "error")
            return redirect(url_for("auth.instructor_login"))

        if not user:
            logger.warning(f"Instructor login failed: User {school_id} not found")
            flash("Invalid instructor credentials.", "error")
            return redirect(url_for("auth.instructor_login"))

        # Check password
        if not check_password_hash(user["password_hash"], password):
            logger.warning(
                f"Instructor login failed: Invalid password for user {school_id}"
            )
            flash("Invalid instructor credentials.", "error")
            return redirect(url_for("auth.instructor_login"))

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
        return redirect(url_for("dashboard.instructor_dashboard"))

    logger.info("Instructor login page accessed")
    return render_template("instructorlogin.html")


# Route: GET/POST "/student-login"
# Used by: studentlogin.html (form posts here); redirects from student-only pages when unauthenticated
# Purpose: Authenticate students; sets session and redirects to /student-dashboard.
@auth_bp.route("/student-login", methods=["GET", "POST"], endpoint="student_login")
def student_login():
    if request.method == "POST":
        school_id = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = "student"

        logger.info(f"Student login attempt for school ID: {school_id}")

        if not school_id or not password:
            logger.warning("Student login failed: Missing credentials")
            flash("Please enter both school ID and password.", "error")
            return redirect(url_for("auth.student_login"))

        # Find user using raw SQL
        try:
            with get_db_connection().cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE school_id = %s", (school_id,))
                user = cursor.fetchone()
        except Exception as e:
            logger.error(f"Database error during student user lookup: {str(e)}")
            flash("An error occurred. Please try again.", "error")
            return redirect(url_for("auth.student_login"))

        if not user:
            logger.warning(f"Student login failed: User {school_id} not found")
            flash("Invalid student credentials.", "error")
            return redirect(url_for("auth.student_login"))

        # Check password
        if not check_password_hash(user["password_hash"], password):
            logger.warning(
                f"Student login failed: Invalid password for user {school_id}"
            )
            flash("Invalid student credentials.", "error")
            return redirect(url_for("auth.student_login"))

        # Check role
        if user["role"] != role:
            logger.warning(f"Student login failed: Role mismatch for user {school_id}")
            flash("Invalid student credentials.", "error")
            return redirect(url_for("auth.student_login"))

        # Login successful
        session["user_id"] = user["id"]
        session["school_id"] = user["school_id"]
        session["role"] = user["role"]
        session.permanent = True

        logger.info(f"Student {school_id} logged in successfully")
        return redirect(url_for("dashboard.student_dashboard"))

    logger.info("Student login page accessed")
    return render_template("studentlogin.html")


# Route: GET "/logout"
# Used by: Logout links/buttons in various templates; session timeouts may redirect here
# Purpose: Clear session and return user to home page.
@auth_bp.route("/logout", endpoint="logout")
def logout():
    user_id = session.get("user_id")
    school_id = session.get("school_id")
    session.clear()
    logger.info(f"User {school_id} (ID: {user_id}) logged out")
    return redirect(url_for("home"))


# Route: GET/POST "/register"
# Used by: register.html (form posts here)
# Purpose: Student self-registration flow creating user, personal_info, and student profile.
@auth_bp.route("/register", methods=["GET", "POST"], endpoint="register")
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
            return redirect(url_for("auth.login"))

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
