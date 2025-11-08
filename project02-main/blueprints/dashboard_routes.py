import logging
from flask import Blueprint, render_template, session, redirect, url_for, flash
from utils.auth_utils import login_required
from utils.db_conn import get_db_connection

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/student-dashboard", endpoint="student_dashboard")
@login_required
def student_dashboard():
    if session.get("role") != "student":
        session.clear()
        flash("Unauthorized access.", "error")
        return redirect(url_for("auth.login"))

    # Get complete user and student data from database
    try:
        with get_db_connection().cursor() as cursor:
            # Get user data
            cursor.execute("SELECT * FROM users WHERE id = %s", (session["user_id"],))
            user_data = cursor.fetchone()

            if not user_data:
                session.clear()
                flash("Session expired. Please log in again.", "error")
                return redirect(url_for("auth.login"))

            # Get student profile data
            cursor.execute(
                """SELECT s.*, pi.first_name, pi.last_name, pi.middle_name, pi.email,
                pi.phone, pi.address, pi.birth_date, pi.gender, pi.emergency_contact_name,
                pi.emergency_contact_phone
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
                                            # additional normalized fields
                                            self.phone = data.get("phone")
                                            self.address = data.get("address")
                                            self.birth_date = data.get("birth_date")
                                            self.gender = data.get("gender")
                                            self.emergency_contact_name = data.get(
                                                "emergency_contact_name"
                                            )
                                            self.emergency_contact_phone = data.get(
                                                "emergency_contact_phone"
                                            )
                                            self.full_name = self.get_full_name()

                                        def get_full_name(self):
                                            if self.middle_name:
                                                return f"{self.first_name} {self.middle_name} {self.last_name}"
                                            return f"{self.first_name} {self.last_name}"

                                    # instantiate PersonalInfo inside the if-block where it's defined
                                    self.personal_info = PersonalInfo(data)

                            def get_full_name(self):
                                if hasattr(self, "personal_info"):
                                    return self.personal_info.full_name
                                return f"Student {self.id}"

                        self.student_profile = StudentProfile(student_data)
                        # expose personal_info at the top-level user object for templates that expect
                        # `user.personal_info` (some templates reference this directly)
                        if hasattr(self.student_profile, "personal_info"):
                            self.personal_info = self.student_profile.personal_info
                    else:
                        self.student_profile = None

            user = UserObject(user_data)

    except Exception as e:
        logger.error(f"Database error during student dashboard: {str(e)}")
        session.clear()
        flash("Session expired. Please log in again.", "error")
        return redirect(url_for("auth.login"))

    logger.info(f"Student dashboard accessed by {session.get('school_id')}")
    return render_template("student_dashboard.html", user=user)


@dashboard_bp.route("/instructor-dashboard", endpoint="instructor_dashboard")
@login_required
def instructor_dashboard():
    if session.get("role") != "instructor":
        session.clear()
        flash("Unauthorized access.", "error")
        return redirect(url_for("auth.login"))

    # Get user data from database
    try:
        with get_db_connection().cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE id = %s", (session["user_id"],))
            user = cursor.fetchone()
    except Exception as e:
        logger.error(f"Database error during instructor dashboard: {str(e)}")
        session.clear()
        flash("Session expired. Please log in again.", "error")
        return redirect(url_for("auth.login"))

    if not user:
        session.clear()
        flash("Session expired. Please log in again.", "error")
        return redirect(url_for("auth.login"))

    logger.info(f"Instructor dashboard accessed by {session.get('school_id')}")
    return render_template("instructor_dashboard.html", user=user)


@dashboard_bp.route("/admin-dashboard", endpoint="admin_dashboard")
@login_required
def admin_dashboard():
    if session.get("role") != "admin":
        session.clear()
        flash("Unauthorized access.", "error")
        return redirect(url_for("auth.login"))

    # Get user data from database
    try:
        with get_db_connection().cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE id = %s", (session["user_id"],))
            user = cursor.fetchone()
    except Exception as e:
        logger.error(f"Database error during admin dashboard: {str(e)}")
        session.clear()
        flash("Session expired. Please log in again.", "error")
        return redirect(url_for("auth.login"))

    if not user:
        session.clear()
        flash("Session expired. Please log in again.", "error")
        return redirect(url_for("auth.login"))

    logger.info(f"Admin dashboard accessed by {session.get('school_id')}")
    return render_template("admin_dashboard.html", user=user)
