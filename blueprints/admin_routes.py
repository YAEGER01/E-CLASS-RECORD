import logging
import traceback
from datetime import datetime
from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash

from utils.db_conn import get_db_connection
from utils.auth_utils import login_required

logger = logging.getLogger(__name__)


admin_bp = Blueprint("admin", __name__)


def _require_admin():
    if session.get("role") != "admin":
        return jsonify({"error": "Access denied. Admin privileges required."}), 403
    return None


@admin_bp.route(
    "/admin/create-instructor", methods=["POST"], endpoint="create_instructor"
)
@login_required
def create_instructor():
    err = _require_admin()
    if err:
        return err

    try:
        # Get form data
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400

        # Extract personal information
        first_name = data.get("firstName", "").strip()
        last_name = data.get("lastName", "").strip()
        middle_name = data.get("middleName", "").strip()
        email = data.get("email", "").strip()
        phone = data.get("phone", "").strip()
        address = data.get("address", "").strip()
        birth_date = data.get("birthDate")
        gender = data.get("gender")
        emergency_contact_name = data.get("emergencyContactName", "").strip()
        emergency_contact_phone = data.get("emergencyContactPhone", "").strip()

        # Extract account information
        school_id = data.get("schoolId", "").strip()
        password = data.get("password", "")
        employee_id = data.get("employeeId", "").strip()

        # Extract professional information
        department = data.get("department", "").strip()
        specialization = data.get("specialization", "").strip()

        # Validation
        errors = []

        # Required field validations
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

        # Password validation: only require passwords match; no complexity/length restriction
        confirm_password = data.get("confirmPassword", "")
        if password != confirm_password:
            errors.append("Passwords do not match")

        # Ensure the ID suffix follows 3 digits for INS-### format
        if (
            not school_id.startswith("INS-")
            or len(school_id) != 7
            or not school_id[4:].isdigit()
        ):
            errors.append("School ID must be in INS-### format")

        # Email validation
        import re

        email_regex = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
        if email and not re.match(email_regex, email):
            errors.append("Please enter a valid email address")

        # Phone validation (if provided)
        if phone and not re.match(r"^[\+]?[0-9\s\-\(\)]{10,}$", phone):
            errors.append("Please enter a valid phone number")

        if errors:
            logger.warning(f"Instructor creation failed: {errors}")
            return jsonify({"success": False, "message": "; ".join(errors)}), 400

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


@admin_bp.route("/api/admin/instructors", methods=["GET"], endpoint="get_instructors")
@login_required
def get_instructors():
    err = _require_admin()
    if err:
        return err

    try:
        conn = get_db_connection()
        conn.ping(reconnect=True)  # Ensure connection is alive

        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT i.id, i.user_id, i.personal_info_id, i.department, i.specialization,
                         i.employee_id, i.hire_date, i.status, i.created_at, i.updated_at,
                         u.school_id, pi.first_name, pi.last_name, pi.email
                FROM instructors i
                JOIN users u ON i.user_id = u.id
                LEFT JOIN personal_info pi ON i.personal_info_id = pi.id
                ORDER BY i.created_at DESC"""
            )
            instructors = cursor.fetchall()

            logger.info(
                f"Fetched {len(instructors) if instructors else 0} instructors from database"
            )

            if not instructors:
                instructors = []

            instructors_data = []
            active_count = 0
            suspended_count = 0

            for instructor in instructors:
                try:
                    # Defensive: handle None values for date fields
                    hire_date = instructor.get("hire_date")
                    created_at = instructor.get("created_at")

                    # Safely convert datetime to ISO format
                    hire_date_str = None
                    if hire_date:
                        try:
                            if hasattr(hire_date, "isoformat"):
                                hire_date_str = hire_date.isoformat()
                            else:
                                hire_date_str = str(hire_date)
                        except Exception as e:
                            logger.warning(f"Could not serialize hire_date: {e}")

                    created_at_str = None
                    if created_at:
                        try:
                            if hasattr(created_at, "isoformat"):
                                created_at_str = created_at.isoformat()
                            else:
                                created_at_str = str(created_at)
                        except Exception as e:
                            logger.warning(f"Could not serialize created_at: {e}")

                    instructor_data = {
                        "id": int(instructor.get("id") or 0),
                        "school_id": str(instructor.get("school_id") or ""),
                        "name": f"{instructor.get('first_name') or ''} {instructor.get('last_name') or ''}".strip()
                        or f"Instructor {instructor.get('id')}",
                        "email": str(instructor.get("email") or "N/A"),
                        "department": str(
                            instructor.get("department") or "Not specified"
                        ),
                        "specialization": str(
                            instructor.get("specialization") or "Not specified"
                        ),
                        "employee_id": str(
                            instructor.get("employee_id") or "Not specified"
                        ),
                        "status": str(instructor.get("status") or "active"),
                        "hire_date": hire_date_str,
                        "created_at": created_at_str,
                        "class_count": 0,
                    }

                    if instructor_data["status"] == "active":
                        active_count += 1
                    else:
                        suspended_count += 1

                    instructors_data.append(instructor_data)
                except Exception as e:
                    logger.error(
                        f"Error processing instructor {instructor.get('id')}: {str(e)}"
                    )
                    logger.error(traceback.format_exc())
                    continue

            recent_instructors = sorted(
                instructors_data, key=lambda x: x["created_at"] or "", reverse=True
            )[:5]

            analytics = {
                "total_instructors": len(instructors_data),
                "active_instructors": active_count,
                "suspended_instructors": suspended_count,
                "recent_instructors": recent_instructors,
            }

        logger.info(
            f"Admin {session.get('school_id')} retrieved instructor analytics: {len(instructors_data)} instructors"
        )
        return jsonify(
            {"success": True, "instructors": instructors_data, "analytics": analytics}
        )

    except Exception as e:
        logger.error(f"Failed to get instructors: {str(e)}")
        logger.error(traceback.format_exc())
        return (
            jsonify({"error": "Failed to retrieve instructors", "details": str(e)}),
            500,
        )


@admin_bp.route(
    "/api/admin/instructors/<int:instructor_id>",
    methods=["GET"],
    endpoint="get_instructor_details",
)
@login_required
def get_instructor_details(instructor_id):
    err = _require_admin()
    if err:
        return err

    try:
        with get_db_connection().cursor() as cursor:
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

            cursor.execute(
                """SELECT id, year, semester, course, section, schedule, class_code, join_code, created_at
                FROM classes WHERE instructor_id = %s""",
                (instructor_id,),
            )
            classes = cursor.fetchall()

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


@admin_bp.route(
    "/api/admin/instructors/<int:instructor_id>/status",
    methods=["PUT"],
    endpoint="update_instructor_status",
)
@login_required
def update_instructor_status(instructor_id):
    err = _require_admin()
    if err:
        return err

    try:
        data = request.get_json()
        new_status = data.get("status")

        if new_status not in ["active", "suspended"]:
            return (
                jsonify({"error": "Invalid status. Must be 'active' or 'suspended'"}),
                400,
            )

        with get_db_connection().cursor() as cursor:
            cursor.execute(
                "SELECT id, status FROM instructors WHERE id = %s", (instructor_id,)
            )
            instructor = cursor.fetchone()

            if not instructor:
                return jsonify({"error": "Instructor not found"}), 404

            old_status = instructor["status"] or "active"

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


@admin_bp.route(
    "/api/admin/instructors/<int:instructor_id>",
    methods=["DELETE"],
    endpoint="delete_instructor",
)
@login_required
def delete_instructor(instructor_id):
    err = _require_admin()
    if err:
        return err

    try:
        with get_db_connection().cursor() as cursor:
            cursor.execute(
                "SELECT i.id, i.user_id, u.school_id FROM instructors i JOIN users u ON i.user_id = u.id WHERE i.id = %s",
                (instructor_id,),
            )
            instructor = cursor.fetchone()

            if not instructor:
                return jsonify({"error": "Instructor not found"}), 404

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

            cursor.execute(
                "SELECT personal_info_id FROM instructors WHERE id = %s",
                (instructor_id,),
            )
            personal_info_result = cursor.fetchone()

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


@admin_bp.route("/api/admin/students", methods=["GET"], endpoint="get_students")
@login_required
def get_students():
    err = _require_admin()
    if err:
        return err

    try:
        with get_db_connection().cursor() as cursor:
            cursor.execute(
                """SELECT s.*, u.school_id, pi.first_name, pi.last_name, pi.email
                FROM students s
                JOIN users u ON s.user_id = u.id
                LEFT JOIN personal_info pi ON s.personal_info_id = pi.id"""
            )
            students = cursor.fetchall()

            students_data = []
            active_count = 0
            suspended_count = 0

            for student in students:
                student_data = {
                    "id": student["id"],
                    "school_id": student["school_id"],
                    "name": f"{student['first_name'] or ''} {student['last_name'] or ''}".strip()
                    or f"Student {student['id']}",
                    "email": student["email"] or "N/A",
                    "course": student["course"] or "Not specified",
                    "track": student["track"] or "Not specified",
                    "year_level": student["year_level"] or "Not specified",
                    "section": student["section"] or "Not specified",
                    "created_at": (
                        student["created_at"].isoformat()
                        if student["created_at"]
                        else None
                    ),
                }

                # For now, assume all students are active (no status field in students table)
                active_count += 1

                students_data.append(student_data)

            recent_students = sorted(
                students_data, key=lambda x: x["created_at"] or "", reverse=True
            )[:5]

            analytics = {
                "total_students": len(students_data),
                "active_students": active_count,
                "suspended_students": suspended_count,
                "recent_students": recent_students,
            }

        logger.info(f"Admin {session.get('school_id')} retrieved student analytics")
        return jsonify(
            {"success": True, "students": students_data, "analytics": analytics}
        )

    except Exception as e:
        logger.error(f"Failed to get students: {str(e)}")
        return jsonify({"error": "Failed to retrieve students"}), 500


@admin_bp.route(
    "/api/admin/students/<int:student_id>",
    methods=["GET"],
    endpoint="get_student_details",
)
@login_required
def get_student_details(student_id):
    err = _require_admin()
    if err:
        return err

    try:
        with get_db_connection().cursor() as cursor:
            cursor.execute(
                """SELECT s.id, s.user_id, s.personal_info_id, s.course, s.track, s.year_level, s.section,
                         s.id_front_path, s.id_back_path, s.face_photo_path, s.created_at,
                         u.school_id, u.role,
                         pi.first_name, pi.last_name, pi.middle_name, pi.email, pi.phone,
                         pi.address, pi.birth_date, pi.gender, pi.emergency_contact_name,
                         pi.emergency_contact_phone
                FROM students s
                JOIN users u ON s.user_id = u.id
                LEFT JOIN personal_info pi ON s.personal_info_id = pi.id
                WHERE s.id = %s""",
                (student_id,),
            )
            student = cursor.fetchone()

            if not student:
                return jsonify({"error": "Student not found"}), 404

            cursor.execute(
                """SELECT sc.id, c.year, c.semester, c.course, c.section, c.schedule, c.class_code, c.join_code, c.created_at
                FROM student_classes sc
                JOIN classes c ON sc.class_id = c.id
                WHERE sc.student_id = %s""",
                (student_id,),
            )
            classes = cursor.fetchall()

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

            student_details = {
                "id": student["id"],
                "school_id": student["school_id"],
                "personal_info": {
                    "first_name": student["first_name"] or "N/A",
                    "last_name": student["last_name"] or "N/A",
                    "middle_name": student["middle_name"],
                    "email": student["email"] or "N/A",
                    "phone": student["phone"],
                    "address": student["address"],
                    "birth_date": (
                        student["birth_date"].isoformat()
                        if student["birth_date"]
                        else None
                    ),
                    "gender": student["gender"],
                    "emergency_contact_name": student["emergency_contact_name"],
                    "emergency_contact_phone": student["emergency_contact_phone"],
                },
                "academic_info": {
                    "course": student["course"],
                    "track": student["track"],
                    "year_level": student["year_level"],
                    "section": student["section"],
                },
                "account_info": {
                    "created_at": (
                        student["created_at"].isoformat()
                        if student["created_at"]
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
            f"Admin {session.get('school_id')} viewed student details: {student['school_id']}"
        )
        return jsonify({"success": True, "student": student_details})

    except Exception as e:
        logger.error(f"Failed to get student details: {str(e)}")
        return jsonify({"error": "Failed to retrieve student details"}), 500


@admin_bp.route(
    "/api/admin/instructors/<int:instructor_id>/classes",
    methods=["GET"],
    endpoint="get_instructor_classes",
)
@login_required
def get_instructor_classes(instructor_id):
    err = _require_admin()
    if err:
        return err

    try:
        logger.info(f"Fetching classes for instructor {instructor_id}")

        conn = get_db_connection()
        conn.ping(reconnect=True)  # Ensure connection is alive
        with conn.cursor() as cursor:
            # Get all classes for this instructor
            cursor.execute(
                """SELECT c.id, c.year, c.semester, c.course, c.section, c.subject,
                         c.schedule, c.class_code, c.join_code, c.created_at
                FROM classes c
                WHERE c.instructor_id = %s
                ORDER BY c.year DESC, c.semester DESC, c.course, c.section""",
                (instructor_id,),
            )
            classes = cursor.fetchall()
            logger.info(f"Found {len(classes)} classes for instructor {instructor_id}")

            classes_with_students = []
            for cls in classes:
                try:
                    # Get students for each class
                    cursor.execute(
                        """SELECT s.id, u.school_id, pi.first_name, pi.last_name,
                                 s.course, s.year_level, s.section, sc.joined_at
                        FROM student_classes sc
                        JOIN students s ON sc.student_id = s.id
                        JOIN users u ON s.user_id = u.id
                        LEFT JOIN personal_info pi ON s.personal_info_id = pi.id
                        WHERE sc.class_id = %s
                        ORDER BY pi.last_name, pi.first_name""",
                        (cls["id"],),
                    )
                    students = cursor.fetchall()

                    # Format class data - ensure all fields are JSON serializable
                    year_val = cls.get("year") or ""
                    formatted_year = str(year_val)[-2:] if year_val else "XX"
                    semester_val = cls.get("semester") or ""
                    formatted_semester = (
                        "1"
                        if semester_val and "1st" in str(semester_val).lower()
                        else (
                            "2"
                            if semester_val and "2nd" in str(semester_val).lower()
                            else "1"
                        )
                    )
                    class_display_id = f"{formatted_year}-{formatted_semester} {cls.get('course') or ''} {cls.get('section') or ''}"

                    # Normalize created_at to string
                    created_at_val = cls.get("created_at")
                    created_at_str = None
                    if created_at_val:
                        try:
                            if hasattr(created_at_val, "isoformat"):
                                created_at_str = created_at_val.isoformat()
                            else:
                                created_at_str = str(created_at_val)
                        except Exception as e:
                            logger.warning(f"Could not serialize created_at: {e}")

                    # Build student list with proper error handling
                    student_list = []
                    for s in students:
                        try:
                            joined_at_val = s.get("joined_at")
                            joined_at_str = None
                            if joined_at_val:
                                if hasattr(joined_at_val, "isoformat"):
                                    joined_at_str = joined_at_val.isoformat()
                                else:
                                    joined_at_str = str(joined_at_val)

                            student_list.append(
                                {
                                    "id": int(s.get("id") or 0),
                                    "school_id": str(s.get("school_id") or ""),
                                    "name": f"{s.get('first_name') or ''} {s.get('last_name') or ''}".strip()
                                    or f"Student {s.get('id') or ''}",
                                    "course": str(s.get("course") or ""),
                                    "year_level": str(s.get("year_level") or ""),
                                    "section": str(s.get("section") or ""),
                                    "joined_at": joined_at_str,
                                }
                            )
                        except Exception as e:
                            logger.error(f"Error processing student {s.get('id')}: {e}")
                            continue

                    classes_with_students.append(
                        {
                            "id": int(cls.get("id") or 0),
                            "class_display_id": str(class_display_id),
                            "year": str(cls.get("year") or ""),
                            "semester": str(cls.get("semester") or ""),
                            "course": str(cls.get("course") or ""),
                            "section": str(cls.get("section") or ""),
                            "subject": str(cls.get("subject") or ""),
                            "schedule": str(cls.get("schedule") or ""),
                            "class_code": str(cls.get("class_code") or ""),
                            "join_code": str(cls.get("join_code") or ""),
                            "created_at": created_at_str,
                            "student_count": len(student_list),
                            "students": student_list,
                        }
                    )
                except Exception as e:
                    logger.error(f"Error processing class {cls.get('id')}: {e}")
                    logger.error(traceback.format_exc())
                    continue

        logger.info(
            f"Admin {session.get('school_id')} retrieved {len(classes_with_students)} classes and students for instructor {instructor_id}"
        )
        return jsonify({"success": True, "classes": classes_with_students})

    except Exception as e:
        logger.error(f"Failed to get instructor classes: {str(e)}")
        logger.error(traceback.format_exc())
        return (
            jsonify(
                {"success": False, "error": "Failed to retrieve instructor classes"}
            ),
            500,
        )


@admin_bp.route("/api/admin/system-analytics", methods=["GET"])
@login_required
def get_system_analytics():
    err = _require_admin()
    if err:
        return err

    try:
        # Check if requesting specific instructor stats
        instructor_id = request.args.get("instructor_id", "").strip()
        print(f"[DEBUG] instructor_id received: {instructor_id}")
        logger.info(f"[DEBUG] instructor_id received: {instructor_id}")

        # Fallback: treat 'undefined', empty, or None as not provided
        if not instructor_id or instructor_id.lower() == "undefined":
            instructor_id = None

        if instructor_id:
            # Return stats for a specific instructor
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    conn = get_db_connection()
                    conn.ping(reconnect=True)  # Ensure connection is alive
                    with conn.cursor() as cursor:
                        query = """
                            SELECT
                                i.id as instructor_id,
                                TRIM(CONCAT(COALESCE(pi.first_name, ''), ' ', COALESCE(pi.middle_name, ''), ' ', COALESCE(pi.last_name, ''))) as instructor_name,
                                i.department,
                                COUNT(DISTINCT c.id) as total_classes,
                                COUNT(DISTINCT CASE WHEN gs.status = 'final' THEN gs.id END) as total_snapshots,
                                COUNT(DISTINCT rg.id) as total_releases,
                                ROUND(COALESCE(AVG(CASE WHEN sc_count.student_count > 0 THEN sc_count.student_count ELSE NULL END), 0), 1) as avg_students_per_class
                            FROM instructors i
                            JOIN users u ON i.user_id = u.id
                            LEFT JOIN personal_info pi ON i.personal_info_id = pi.id
                            LEFT JOIN classes c ON i.id = c.instructor_id
                            LEFT JOIN grade_snapshots gs ON c.id = gs.class_id AND gs.status = 'final'
                            LEFT JOIN released_grades rg ON c.id = rg.class_id
                            LEFT JOIN (
                                SELECT c.id as class_id, COUNT(sc.student_id) as student_count
                                FROM classes c
                                LEFT JOIN student_classes sc ON c.id = sc.class_id
                                GROUP BY c.id
                            ) sc_count ON c.id = sc_count.class_id
                            WHERE i.id = %s AND i.status = 'active'
                            GROUP BY i.id, pi.first_name, pi.middle_name, pi.last_name, i.department
                        """

                        cursor.execute(query, (instructor_id,))
                        result = cursor.fetchone()

                        if result:
                            instructor_name = result["instructor_name"].strip()
                            if not instructor_name:
                                instructor_name = (
                                    f"Instructor {result['instructor_id']}"
                                )

                            analytics_data = [
                                {
                                    "instructor_id": int(result["instructor_id"]),
                                    "instructor_name": instructor_name,
                                    "department": str(
                                        result["department"] or "Not specified"
                                    ),
                                    "total_classes": int(result["total_classes"] or 0),
                                    "total_snapshots": int(
                                        result["total_snapshots"] or 0
                                    ),
                                    "total_releases": int(
                                        result["total_releases"] or 0
                                    ),
                                    "avg_students_per_class": float(
                                        result["avg_students_per_class"] or 0
                                    ),
                                }
                            ]
                        else:
                            analytics_data = []

                    log_instructor = (
                        instructor_id if instructor_id else "None or not provided"
                    )
                    logger.info(
                        f"Admin {session.get('school_id')} retrieved analytics for instructor {log_instructor}"
                    )
                    print(
                        f"[DEBUG] Analytics for instructor_id={log_instructor}: {analytics_data}"
                    )
                    return jsonify({"success": True, "analytics": analytics_data})
                except Exception as e:
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed to get analytics for instructor {instructor_id}: {str(e)}"
                    )
                    if attempt < max_retries - 1:
                        import time

                        time.sleep(1)  # Wait 1 second before retry
                        continue
                    else:
                        logger.error(
                            f"Failed to get analytics for instructor {instructor_id} after {max_retries} attempts: {str(e)}"
                        )
                        logger.error(traceback.format_exc())
                        print(
                            f"[ERROR] Failed to get analytics for instructor {instructor_id}: {str(e)}"
                        )
                        print(traceback.format_exc())
                        return (
                            jsonify(
                                {
                                    "success": False,
                                    "error": "Failed to retrieve instructor analytics",
                                }
                            ),
                            500,
                        )

        else:
            # Original system-wide analytics (for backward compatibility)
            # Get filter parameters
            instructor_filter = request.args.get("instructor", "").strip()
            year_filter = request.args.get("year", "").strip()
            course_filter = request.args.get("course", "").strip()
            section_filter = request.args.get("section", "").strip()
            subject_filter = request.args.get("subject", "").strip()

            try:
                with get_db_connection().cursor() as cursor:
                    # Build the main query with filters
                    query = """
                        SELECT
                            i.id as instructor_id,
                            TRIM(CONCAT(COALESCE(pi.first_name, ''), ' ', COALESCE(pi.middle_name, ''), ' ', COALESCE(pi.last_name, ''))) as instructor_name,
                            i.department,
                            COUNT(DISTINCT c.id) as total_classes,
                            COUNT(DISTINCT CASE WHEN gs.status = 'final' THEN gs.id END) as total_snapshots,
                            COUNT(DISTINCT rg.id) as total_releases,
                            ROUND(COALESCE(AVG(CASE WHEN sc_count.student_count > 0 THEN sc_count.student_count ELSE NULL END), 0), 1) as avg_students_per_class
                        FROM instructors i
                        JOIN users u ON i.user_id = u.id
                        LEFT JOIN personal_info pi ON i.personal_info_id = pi.id
                        LEFT JOIN classes c ON i.id = c.instructor_id
                        LEFT JOIN grade_snapshots gs ON c.id = gs.class_id AND gs.status = 'final'
                        LEFT JOIN released_grades rg ON c.id = rg.class_id
                        LEFT JOIN (
                            SELECT c.id as class_id, COUNT(sc.student_id) as student_count
                            FROM classes c
                            LEFT JOIN student_classes sc ON c.id = sc.class_id
                            GROUP BY c.id
                        ) sc_count ON c.id = sc_count.class_id
                        WHERE i.status = 'active'
                    """

                    params = []

                    # Apply filters
                    if instructor_filter:
                        query += " AND TRIM(CONCAT(COALESCE(pi.first_name, ''), ' ', COALESCE(pi.middle_name, ''), ' ', COALESCE(pi.last_name, ''))) LIKE %s"
                        params.append(f"%{instructor_filter}%")

                    if year_filter:
                        query += " AND c.year = %s"
                        params.append(year_filter)

                    if course_filter:
                        query += " AND c.course = %s"
                        params.append(course_filter)

                    if section_filter:
                        query += " AND c.section = %s"
                        params.append(section_filter)

                    if subject_filter:
                        query += " AND c.subject LIKE %s"
                        params.append(f"%{subject_filter}%")

                    query += """
                        GROUP BY i.id, pi.first_name, pi.middle_name, pi.last_name, i.department
                        HAVING COUNT(DISTINCT c.id) > 0
                        ORDER BY instructor_name
                    """

                    cursor.execute(query, params)
                    results = cursor.fetchall()

                    analytics_data = []
                    for row in results:
                        instructor_name = row["instructor_name"].strip()
                        if not instructor_name:
                            instructor_name = f"Instructor {row['instructor_id']}"

                        analytics_data.append(
                            {
                                "instructor_id": int(row["instructor_id"]),
                                "instructor_name": instructor_name,
                                "department": str(row["department"] or "Not specified"),
                                "total_classes": int(row["total_classes"] or 0),
                                "total_snapshots": int(row["total_snapshots"] or 0),
                                "total_releases": int(row["total_releases"] or 0),
                                "avg_students_per_class": float(
                                    row["avg_students_per_class"] or 0
                                ),
                            }
                        )

                logger.info(
                    f"Admin {session.get('school_id')} retrieved system analytics with filters: instructor={instructor_filter}, year={year_filter}, course={course_filter}, section={section_filter}, subject={subject_filter}"
                )
                print(
                    f"[DEBUG] System analytics with filters: instructor={instructor_filter}, year={year_filter}, course={course_filter}, section={section_filter}, subject={subject_filter}"
                )
                print(f"[DEBUG] Analytics data: {analytics_data}")
                return jsonify({"success": True, "analytics": analytics_data})
            except Exception as e:
                logger.error(f"Failed to get system analytics: {str(e)}")
                logger.error(traceback.format_exc())
                print(f"[ERROR] Failed to get system analytics: {str(e)}")
                print(traceback.format_exc())
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "Failed to retrieve system analytics",
                        }
                    ),
                    500,
                )

    except Exception as e:
        logger.error(f"Failed to get system analytics: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": "Failed to retrieve system analytics"}), 500


@admin_bp.route(
    "/api/admin/class-overview", methods=["GET"], endpoint="get_class_overview"
)
@login_required
def get_class_overview():
    err = _require_admin()
    if err:
        return err

    try:
        with get_db_connection().cursor() as cursor:
            # 1. Total classes per semester
            cursor.execute(
                """
                SELECT
                    CONCAT(year, ' - ', semester) as semester_key,
                    COUNT(*) as total_classes
                FROM classes
                GROUP BY year, semester
                ORDER BY year DESC, semester DESC
            """
            )
            semester_stats = cursor.fetchall()

            # 2. Classes per department/course/track
            cursor.execute(
                """
                SELECT
                    COALESCE(i.department, 'Not Assigned') as department,
                    COUNT(DISTINCT c.id) as total_classes
                FROM classes c
                LEFT JOIN instructors i ON c.instructor_id = i.id
                GROUP BY i.department
                ORDER BY total_classes DESC
            """
            )
            department_stats = cursor.fetchall()

            cursor.execute(
                """
                SELECT
                    c.course,
                    COUNT(*) as total_classes
                FROM classes c
                GROUP BY c.course
                ORDER BY total_classes DESC
            """
            )
            course_stats = cursor.fetchall()

            # 3. Number of assessments per class
            cursor.execute(
                """
                SELECT
                    c.id,
                    c.year,
                    c.semester,
                    c.course,
                    c.section,
                    COUNT(ga.id) as assessment_count,
                    CASE WHEN gs.id IS NOT NULL THEN 'Yes' ELSE 'No' END as has_structure
                FROM classes c
                LEFT JOIN grade_structures gs ON c.id = gs.class_id
                LEFT JOIN grade_categories gc ON gs.id = gc.structure_id
                LEFT JOIN grade_subcategories gsc ON gc.id = gsc.category_id
                LEFT JOIN grade_assessments ga ON gsc.id = ga.subcategory_id
                GROUP BY c.id, c.year, c.semester, c.course, c.section, gs.id
                ORDER BY c.year DESC, c.semester DESC, c.course, c.section
            """
            )
            assessment_stats = cursor.fetchall()

            # 4. Students enrolled per class
            cursor.execute(
                """
                SELECT
                    c.id,
                    c.year,
                    c.semester,
                    c.course,
                    c.section,
                    COUNT(sc.student_id) as enrolled_students
                FROM classes c
                LEFT JOIN student_classes sc ON c.id = sc.class_id
                GROUP BY c.id, c.year, c.semester, c.course, c.section
                ORDER BY c.year DESC, c.semester DESC, c.course, c.section
            """
            )
            enrollment_stats = cursor.fetchall()

            # 5. Grading structure completion percentage
            cursor.execute(
                """
                SELECT
                    c.id,
                    c.year,
                    c.semester,
                    c.course,
                    c.section,
                    CASE
                        WHEN gs.id IS NULL THEN 0
                        WHEN (
                            SELECT COUNT(*) FROM grade_categories WHERE structure_id = gs.id
                        ) = 0 THEN 25
                        WHEN (
                            SELECT COUNT(*) FROM grade_subcategories WHERE category_id IN (
                                SELECT id FROM grade_categories WHERE structure_id = gs.id
                            )
                        ) = 0 THEN 50
                        WHEN (
                            SELECT COUNT(*) FROM grade_assessments WHERE subcategory_id IN (
                                SELECT id FROM grade_subcategories WHERE category_id IN (
                                    SELECT id FROM grade_categories WHERE structure_id = gs.id
                                )
                            )
                        ) = 0 THEN 75
                        ELSE 100
                    END as completion_percentage,
                    CASE
                        WHEN gs.id IS NULL THEN 'No Structure'
                        WHEN (
                            SELECT COUNT(*) FROM grade_categories WHERE structure_id = gs.id
                        ) = 0 THEN 'Categories Missing'
                        WHEN (
                            SELECT COUNT(*) FROM grade_subcategories WHERE category_id IN (
                                SELECT id FROM grade_categories WHERE structure_id = gs.id
                            )
                        ) = 0 THEN 'Subcategories Missing'
                        WHEN (
                            SELECT COUNT(*) FROM grade_assessments WHERE subcategory_id IN (
                                SELECT id FROM grade_subcategories WHERE category_id IN (
                                    SELECT id FROM grade_categories WHERE structure_id = gs.id
                                )
                            )
                        ) = 0 THEN 'Assessments Missing'
                        ELSE 'Complete'
                    END as completion_status
                FROM classes c
                LEFT JOIN grade_structures gs ON c.id = gs.class_id
                ORDER BY c.year DESC, c.semester DESC, c.course, c.section
            """
            )
            completion_stats = cursor.fetchall()

        # Calculate summary statistics
        total_classes = len(enrollment_stats)
        total_students = sum(stat["enrolled_students"] for stat in enrollment_stats)
        avg_students_per_class = (
            round(total_students / total_classes, 1) if total_classes > 0 else 0
        )

        completion_percentages = [
            stat["completion_percentage"] for stat in completion_stats
        ]
        avg_completion = (
            round(sum(completion_percentages) / len(completion_percentages), 1)
            if completion_percentages
            else 0
        )

        summary_stats = {
            "total_classes": total_classes,
            "total_students": total_students,
            "avg_students_per_class": avg_students_per_class,
            "avg_completion_percentage": avg_completion,
        }

        logger.info(
            f"Admin {session.get('school_id')} retrieved class overview analytics"
        )
        return jsonify(
            {
                "success": True,
                "summary": summary_stats,
                "semester_stats": semester_stats,
                "department_stats": department_stats,
                "course_stats": course_stats,
                "assessment_stats": assessment_stats,
                "enrollment_stats": enrollment_stats,
                "completion_stats": completion_stats,
            }
        )

    except Exception as e:
        logger.error(f"Failed to get class overview: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": "Failed to retrieve class overview"}), 500


@admin_bp.route(
    "/api/admin/grade-release-monitoring",
    methods=["GET"],
    endpoint="get_grade_release_monitoring",
)
@login_required
def get_grade_release_monitoring():
    err = _require_admin()
    if err:
        return err

    try:
        with get_db_connection().cursor() as cursor:
            # Get all classes with instructor info and grade release status
            cursor.execute(
                """
                SELECT
                    c.id,
                    c.year,
                    c.semester,
                    c.course,
                    c.section,
                    c.subject,
                    c.schedule,
                    c.class_code,
                    c.join_code,
                    c.created_at,
                    i.id as instructor_id,
                    TRIM(CONCAT(COALESCE(pi.first_name, ''), ' ', COALESCE(pi.middle_name, ''), ' ', COALESCE(pi.last_name, ''))) as instructor_name,
                    i.department,
                    CASE WHEN rg.id IS NOT NULL THEN 1 ELSE 0 END as grade_released,
                    rg.released_at as release_date,
                    rg.created_at as release_created_at,
                    COUNT(DISTINCT sc.student_id) as total_students,
                    COUNT(DISTINCT CASE WHEN sg.student_id IS NOT NULL THEN sg.student_id END) as graded_students
                FROM classes c
                LEFT JOIN instructors i ON c.instructor_id = i.id
                LEFT JOIN personal_info pi ON i.personal_info_id = pi.id
                LEFT JOIN released_grades rg ON c.id = rg.class_id
                LEFT JOIN student_classes sc ON c.id = sc.class_id
                LEFT JOIN student_grades sg ON c.id = sg.class_id
                GROUP BY c.id, c.year, c.semester, c.course, c.section, c.subject, c.schedule,
                         c.class_code, c.join_code, c.created_at, i.id, pi.first_name, pi.middle_name,
                         pi.last_name, i.department, rg.id, rg.released_at, rg.created_at
                ORDER BY c.year DESC, c.semester DESC, c.course, c.section
                """
            )
            classes = cursor.fetchall()

            # Calculate summary statistics
            total_classes = len(classes)
            released_classes = sum(1 for cls in classes if cls["grade_released"])
            pending_classes = total_classes - released_classes

            # Calculate ungraded students (students enrolled but not graded)
            total_students = sum(cls["total_students"] for cls in classes)
            graded_students = sum(cls["graded_students"] for cls in classes)
            ungraded_students = total_students - graded_students

            # Process classes data
            classes_data = []
            for cls in classes:
                # Format class display ID
                year_val = cls.get("year") or ""
                formatted_year = str(year_val)[-2:] if year_val else "XX"
                semester_val = cls.get("semester") or ""
                formatted_semester = (
                    "1"
                    if semester_val and "1st" in str(semester_val).lower()
                    else (
                        "2"
                        if semester_val and "2nd" in str(semester_val).lower()
                        else "1"
                    )
                )
                class_display_id = f"{formatted_year}-{formatted_semester} {cls.get('course') or ''} {cls.get('section') or ''}"

                # Calculate ungraded students for this class
                ungraded_in_class = cls["total_students"] - cls["graded_students"]

                # Find oldest pending grade (if any)
                oldest_pending = None
                if not cls["grade_released"] and cls["total_students"] > 0:
                    # This would require additional query to find oldest ungraded student enrollment
                    # For now, we'll use class creation date as approximation
                    oldest_pending = cls["created_at"]

                classes_data.append(
                    {
                        "id": cls["id"],
                        "class_display_id": class_display_id,
                        "year": str(cls.get("year") or ""),
                        "semester": str(cls.get("semester") or ""),
                        "course": str(cls.get("course") or ""),
                        "section": str(cls.get("section") or ""),
                        "subject": str(cls.get("subject") or ""),
                        "schedule": str(cls.get("schedule") or ""),
                        "class_code": str(cls.get("class_code") or ""),
                        "join_code": str(cls.get("join_code") or ""),
                        "instructor_id": cls["instructor_id"],
                        "instructor_name": cls["instructor_name"].strip()
                        or f"Instructor {cls['instructor_id']}",
                        "department": str(cls.get("department") or "Not specified"),
                        "grade_released": bool(cls["grade_released"]),
                        "release_date": (
                            cls["release_date"].isoformat()
                            if cls["release_date"]
                            else None
                        ),
                        "total_students": cls["total_students"],
                        "graded_students": cls["graded_students"],
                        "ungraded_students": ungraded_in_class,
                        "oldest_pending": (
                            oldest_pending.isoformat() if oldest_pending else None
                        ),
                    }
                )

            summary = {
                "total_classes": total_classes,
                "released_classes": released_classes,
                "pending_classes": pending_classes,
                "ungraded_students": ungraded_students,
            }

        logger.info(
            f"Admin {session.get('school_id')} retrieved grade release monitoring data"
        )
        return jsonify({"success": True, "summary": summary, "classes": classes_data})

    except Exception as e:
        logger.error(f"Failed to get grade release monitoring data: {str(e)}")
        logger.error(traceback.format_exc())
        return (
            jsonify({"error": "Failed to retrieve grade release monitoring data"}),
            500,
        )
