import logging
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
        with get_db_connection().cursor() as cursor:
            cursor.execute(
                """SELECT i.*, u.school_id, pi.first_name, pi.last_name, pi.email
                FROM instructors i
                JOIN users u ON i.user_id = u.id
                LEFT JOIN personal_info pi ON i.personal_info_id = pi.id"""
            )
            instructors = cursor.fetchall()

            if not instructors:
                instructors = []

            instructors_data = []
            active_count = 0
            suspended_count = 0

            for instructor in instructors:
                # Defensive: handle None values for date fields
                hire_date = instructor.get("hire_date")
                created_at = instructor.get("created_at")
                instructor_data = {
                    "id": instructor.get("id"),
                    "school_id": instructor.get("school_id"),
                    "name": f"{instructor.get('first_name', '')} {instructor.get('last_name', '')}".strip()
                    or f"Instructor {instructor.get('id')}",
                    "email": instructor.get("email") or "N/A",
                    "department": instructor.get("department") or "Not specified",
                    "specialization": instructor.get("specialization")
                    or "Not specified",
                    "employee_id": instructor.get("employee_id") or "Not specified",
                    "status": instructor.get("status") or "active",
                    "hire_date": hire_date.isoformat() if hire_date else None,
                    "created_at": created_at.isoformat() if created_at else None,
                    "class_count": 0,
                }

                if instructor_data["status"] == "active":
                    active_count += 1
                else:
                    suspended_count += 1

                instructors_data.append(instructor_data)

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
