import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash

from utils.db_conn import get_db_connection
from utils.auth_utils import login_required, log_admin_action

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
        # Removed strict uppercase/lowercase requirements per admin preference
        # if not any(c.isupper() for c in password):
        #     errors.append("Password must contain at least one uppercase letter")
        # if not any(c.islower() for c in password):
        #     errors.append("Password must contain at least one lowercase letter")
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
            log_admin_action(
                "CREATE_INSTRUCTOR",
                "instructor",
                user_id,
                f"Created instructor: {first_name} {last_name} ({school_id}) - Department: {department}",
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
        log_admin_action(
            "UPDATE_INSTRUCTOR_STATUS",
            "instructor",
            instructor_id,
            f"Status changed from {old_status} to {new_status}",
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
        log_admin_action(
            "DELETE_INSTRUCTOR",
            "instructor",
            instructor_id,
            f"Deleted instructor: {instructor['school_id']}",
        )
        return jsonify({"success": True, "message": "Instructor deleted successfully"})

    except Exception as e:
        get_db_connection().rollback()
        logger.error(f"Failed to delete instructor: {str(e)}")
        return jsonify({"error": "Failed to delete instructor"}), 500


@admin_bp.route("/api/admin/audit-logs", methods=["GET"], endpoint="get_audit_logs")
@login_required
def get_audit_logs():
    err = _require_admin()
    if err:
        return err

    try:
        # Get query parameters
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 50))
        action_filter = request.args.get("action")
        resource_type_filter = request.args.get("resource_type")
        admin_filter = request.args.get("admin")

        offset = (page - 1) * per_page

        # Build query
        query = """
            SELECT id, admin_school_id, action, resource_type, resource_id, details,
                   ip_address, timestamp
            FROM audit_logs
            WHERE 1=1
        """
        params = []

        if action_filter:
            query += " AND action = %s"
            params.append(action_filter)

        if resource_type_filter:
            query += " AND resource_type = %s"
            params.append(resource_type_filter)

        if admin_filter:
            query += " AND admin_school_id = %s"
            params.append(admin_filter)

        query += " ORDER BY timestamp DESC LIMIT %s OFFSET %s"
        params.extend([per_page, offset])

        with get_db_connection().cursor() as cursor:
            cursor.execute(query, params)
            logs = cursor.fetchall()

            # Get total count for pagination
            count_query = """
                SELECT COUNT(*) as total
                FROM audit_logs
                WHERE 1=1
            """
            count_params = []

            if action_filter:
                count_query += " AND action = %s"
                count_params.append(action_filter)

            if resource_type_filter:
                count_query += " AND resource_type = %s"
                count_params.append(resource_type_filter)

            if admin_filter:
                count_query += " AND admin_school_id = %s"
                count_params.append(admin_filter)

            cursor.execute(count_query, count_params)
            total_count = cursor.fetchone()["total"]

        # Format logs
        formatted_logs = []
        for log in logs:
            formatted_logs.append(
                {
                    "id": log["id"],
                    "admin_school_id": log["admin_school_id"],
                    "action": log["action"],
                    "resource_type": log["resource_type"],
                    "resource_id": log["resource_id"],
                    "details": log["details"],
                    "ip_address": log["ip_address"],
                    "timestamp": (
                        log["timestamp"].isoformat() if log["timestamp"] else None
                    ),
                }
            )

        total_pages = (total_count + per_page - 1) // per_page

        logger.info(
            f"Admin {session.get('school_id')} retrieved audit logs (page {page})"
        )
        return jsonify(
            {
                "success": True,
                "logs": formatted_logs,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total_count": total_count,
                    "total_pages": total_pages,
                },
            }
        )

    except Exception as e:
        logger.error(f"Failed to get audit logs: {str(e)}")
        return jsonify({"error": "Failed to retrieve audit logs"}), 500


@admin_bp.route(
    "/api/admin/audit-logs/stats", methods=["GET"], endpoint="get_audit_stats"
)
@login_required
def get_audit_stats():
    err = _require_admin()
    if err:
        return err

    try:
        with get_db_connection().cursor() as cursor:
            # Get action counts
            cursor.execute(
                """
                SELECT action, COUNT(*) as count
                FROM audit_logs
                GROUP BY action
                ORDER BY count DESC
            """
            )
            action_stats = cursor.fetchall()

            # Get resource type counts
            cursor.execute(
                """
                SELECT resource_type, COUNT(*) as count
                FROM audit_logs
                GROUP BY resource_type
                ORDER BY count DESC
            """
            )
            resource_stats = cursor.fetchall()

            # Get recent activity (last 7 days)
            cursor.execute(
                """
                SELECT DATE(timestamp) as date, COUNT(*) as count
                FROM audit_logs
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
            """
            )
            recent_activity = cursor.fetchall()

            # Get admin activity
            cursor.execute(
                """
                SELECT admin_school_id, COUNT(*) as count
                FROM audit_logs
                GROUP BY admin_school_id
                ORDER BY count DESC
            """
            )
            admin_stats = cursor.fetchall()

        stats = {
            "action_stats": [
                {"action": stat["action"], "count": stat["count"]}
                for stat in action_stats
            ],
            "resource_stats": [
                {"resource_type": stat["resource_type"], "count": stat["count"]}
                for stat in resource_stats
            ],
            "recent_activity": [
                {"date": str(stat["date"]), "count": stat["count"]}
                for stat in recent_activity
            ],
            "admin_stats": [
                {"admin_school_id": stat["admin_school_id"], "count": stat["count"]}
                for stat in admin_stats
            ],
        }

        logger.info(f"Admin {session.get('school_id')} retrieved audit statistics")
        return jsonify({"success": True, "stats": stats})

    except Exception as e:
        logger.error(f"Failed to get audit stats: {str(e)}")
        return jsonify({"error": "Failed to retrieve audit statistics"}), 500


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


@admin_bp.route("/api/admin/reports/users", methods=["GET"], endpoint="get_user_report")
@login_required
def get_user_report():
    err = _require_admin()
    if err:
        return err

    try:
        with get_db_connection().cursor() as cursor:
            # Get user counts by role
            cursor.execute(
                """
                SELECT role, COUNT(*) as count
                FROM users
                GROUP BY role
            """
            )
            user_counts = cursor.fetchall()

            # Get instructor counts by department
            cursor.execute(
                """
                SELECT i.department, COUNT(*) as count
                FROM instructors i
                GROUP BY i.department
                ORDER BY count DESC
            """
            )
            department_counts = cursor.fetchall()

            # Get student counts by course
            cursor.execute(
                """
                SELECT s.course, COUNT(*) as count
                FROM students s
                GROUP BY s.course
                ORDER BY count DESC
            """
            )
            course_counts = cursor.fetchall()

            # Get student counts by year level
            cursor.execute(
                """
                SELECT s.year_level, COUNT(*) as count
                FROM students s
                GROUP BY s.year_level
                ORDER BY s.year_level
            """
            )
            year_counts = cursor.fetchall()

            # Get recent user registrations (last 30 days)
            cursor.execute(
                """
                SELECT DATE(created_at) as date, role, COUNT(*) as count
                FROM users
                WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                GROUP BY DATE(created_at), role
                ORDER BY date DESC
            """
            )
            recent_registrations = cursor.fetchall()

        report = {
            "user_counts": [
                {"role": uc["role"], "count": uc["count"]} for uc in user_counts
            ],
            "department_counts": [
                {
                    "department": dc["department"] or "Not specified",
                    "count": dc["count"],
                }
                for dc in department_counts
            ],
            "course_counts": [
                {"course": cc["course"] or "Not specified", "count": cc["count"]}
                for cc in course_counts
            ],
            "year_counts": [
                {"year_level": yc["year_level"], "count": yc["count"]}
                for yc in year_counts
            ],
            "recent_registrations": [
                {"date": str(rr["date"]), "role": rr["role"], "count": rr["count"]}
                for rr in recent_registrations
            ],
            "generated_at": datetime.now().isoformat(),
        }

        log_admin_action("GENERATE_REPORT", "report", None, "Generated user report")
        logger.info(f"Admin {session.get('school_id')} generated user report")
        return jsonify({"success": True, "report": report})

    except Exception as e:
        logger.error(f"Failed to generate user report: {str(e)}")
        return jsonify({"error": "Failed to generate user report"}), 500


@admin_bp.route(
    "/api/admin/reports/classes", methods=["GET"], endpoint="get_class_report"
)
@login_required
def get_class_report():
    err = _require_admin()
    if err:
        return err

    try:
        with get_db_connection().cursor() as cursor:
            # Get class counts by year/semester
            cursor.execute(
                """
                SELECT year, semester, COUNT(*) as count
                FROM classes
                GROUP BY year, semester
                ORDER BY year DESC, semester DESC
            """
            )
            class_counts = cursor.fetchall()

            # Get class counts by course
            cursor.execute(
                """
                SELECT course, COUNT(*) as count
                FROM classes
                GROUP BY course
                ORDER BY count DESC
            """
            )
            course_class_counts = cursor.fetchall()

            # Get instructor class loads
            cursor.execute(
                """
                SELECT i.id, CONCAT(pi.first_name, ' ', pi.last_name) as name,
                       COUNT(c.id) as class_count
                FROM instructors i
                LEFT JOIN personal_info pi ON i.personal_info_id = pi.id
                LEFT JOIN classes c ON i.id = c.instructor_id
                GROUP BY i.id, pi.first_name, pi.last_name
                ORDER BY class_count DESC
            """
            )
            instructor_loads = cursor.fetchall()

            # Get class enrollment statistics
            cursor.execute(
                """
                SELECT c.id, c.course, c.section, c.year, c.semester,
                       COUNT(sc.student_id) as enrolled_count
                FROM classes c
                LEFT JOIN student_classes sc ON c.id = sc.class_id
                GROUP BY c.id, c.course, c.section, c.year, c.semester
                ORDER BY enrolled_count DESC
            """
            )
            enrollment_stats = cursor.fetchall()

        report = {
            "class_counts": [
                {"year": cc["year"], "semester": cc["semester"], "count": cc["count"]}
                for cc in class_counts
            ],
            "course_class_counts": [
                {"course": ccc["course"], "count": ccc["count"]}
                for ccc in course_class_counts
            ],
            "instructor_loads": [
                {
                    "instructor_id": il["id"],
                    "name": il["name"] or f"Instructor {il['id']}",
                    "class_count": il["class_count"],
                }
                for il in instructor_loads
            ],
            "enrollment_stats": [
                {
                    "class_id": es["id"],
                    "course": es["course"],
                    "section": es["section"],
                    "year": es["year"],
                    "semester": es["semester"],
                    "enrolled_count": es["enrolled_count"],
                }
                for es in enrollment_stats
            ],
            "generated_at": datetime.now().isoformat(),
        }

        log_admin_action("GENERATE_REPORT", "report", None, "Generated class report")
        logger.info(f"Admin {session.get('school_id')} generated class report")
        return jsonify({"success": True, "report": report})

    except Exception as e:
        logger.error(f"Failed to generate class report: {str(e)}")
        return jsonify({"error": "Failed to generate class report"}), 500


@admin_bp.route(
    "/api/admin/reports/system", methods=["GET"], endpoint="get_system_report"
)
@login_required
def get_system_report():
    err = _require_admin()
    if err:
        return err

    try:
        with get_db_connection().cursor() as cursor:
            # Get database table sizes - handle schema change errors gracefully
            try:
                cursor.execute(
                    """
                    SELECT table_name, table_rows, data_length, index_length
                    FROM information_schema.tables
                    WHERE table_schema = DATABASE()
                    ORDER BY data_length DESC
                """
                )
                table_sizes = cursor.fetchall()
            except Exception as schema_error:
                logger.warning(
                    f"Could not retrieve table sizes due to schema change: {str(schema_error)}"
                )
                # Provide fallback data
                table_sizes = [
                    {
                        "table_name": "schema_unavailable",
                        "table_rows": 0,
                        "data_length": 0,
                        "index_length": 0,
                    }
                ]

            # Get audit log statistics - handle case where table might not exist yet
            try:
                cursor.execute(
                    """
                    SELECT COUNT(*) as total_logs,
                           COUNT(DISTINCT admin_id) as unique_admins,
                           MAX(timestamp) as last_activity
                    FROM audit_logs
                """
                )
                audit_stats = cursor.fetchone()
            except Exception as audit_error:
                logger.warning(
                    f"Could not retrieve audit stats (table may not exist): {str(audit_error)}"
                )
                # Provide fallback data
                audit_stats = {
                    "total_logs": 0,
                    "unique_admins": 0,
                    "last_activity": None,
                }

            # Get user activity (login counts - approximate from audit logs)
            try:
                cursor.execute(
                    """
                    SELECT COUNT(*) as total_actions,
                           COUNT(DISTINCT DATE(timestamp)) as active_days
                    FROM audit_logs
                    WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                """
                )
                activity_stats = cursor.fetchone()
            except Exception as activity_error:
                logger.warning(
                    f"Could not retrieve activity stats: {str(activity_error)}"
                )
                # Provide fallback data
                activity_stats = {"total_actions": 0, "active_days": 0}

        report = {
            "database_stats": {
                "table_sizes": [
                    {
                        "table": ts["table_name"],
                        "rows": ts["table_rows"],
                        "data_size_kb": round((ts["data_length"] or 0) / 1024, 2),
                        "index_size_kb": round((ts["index_length"] or 0) / 1024, 2),
                    }
                    for ts in table_sizes
                ],
                "note": "Database statistics may be unavailable if schema changes occurred during the session",
            },
            "audit_stats": {
                "total_logs": audit_stats["total_logs"],
                "unique_admins": audit_stats["unique_admins"],
                "last_activity": (
                    audit_stats["last_activity"].isoformat()
                    if audit_stats["last_activity"]
                    else None
                ),
                "note": "Audit statistics may be zero if the audit_logs table was recently created",
            },
            "activity_stats": {
                "total_actions_30d": activity_stats["total_actions"],
                "active_days_30d": activity_stats["active_days"],
            },
            "generated_at": datetime.now().isoformat(),
        }

        log_admin_action("GENERATE_REPORT", "report", None, "Generated system report")
        logger.info(f"Admin {session.get('school_id')} generated system report")
        return jsonify({"success": True, "report": report})

    except Exception as e:
        logger.error(f"Failed to generate system report: {str(e)}")
        return jsonify({"error": "Failed to generate system report"}), 500


@admin_bp.route("/api/admin/audit-logs", methods=["GET"], endpoint="get_audit_logs_api")
@login_required
def get_audit_logs():
    err = _require_admin()
    if err:
        return err

    try:
        # Get query parameters for filtering
        action_filter = request.args.get("action")
        resource_type_filter = request.args.get("resource_type")
        date_from = request.args.get("date_from")
        date_to = request.args.get("date_to")
        limit = request.args.get("limit", 1000, type=int)

        with get_db_connection().cursor() as cursor:
            try:
                query = """
                    SELECT id, admin_school_id, action, resource_type, resource_id, details,
                           ip_address, timestamp
                    FROM audit_logs
                    WHERE 1=1
                """
                params = []

                if action_filter:
                    query += " AND action = %s"
                    params.append(action_filter)

                if resource_type_filter:
                    query += " AND resource_type = %s"
                    params.append(resource_type_filter)

                if date_from:
                    query += " AND DATE(timestamp) >= %s"
                    params.append(date_from)

                if date_to:
                    query += " AND DATE(timestamp) <= %s"
                    params.append(date_to)

                query += " ORDER BY timestamp DESC LIMIT %s"
                params.append(limit)

                cursor.execute(query, params)
                audit_logs = cursor.fetchall()
            except Exception as table_error:
                logger.warning(
                    f"Audit logs table may not exist yet: {str(table_error)}"
                )
                # Return empty list if table doesn't exist
                audit_logs = []

        audit_logs_data = []
        for log in audit_logs:
            audit_logs_data.append(
                {
                    "id": log["id"],
                    "admin_school_id": log["admin_school_id"],
                    "action": log["action"],
                    "resource_type": log["resource_type"],
                    "resource_id": log["resource_id"],
                    "details": log["details"],
                    "ip_address": log["ip_address"],
                    "timestamp": (
                        log["timestamp"].isoformat() if log["timestamp"] else None
                    ),
                }
            )

        log_admin_action(
            "VIEW_AUDIT_LOGS",
            "audit_log",
            None,
            f"Viewed audit logs with filters: action={action_filter}, resource_type={resource_type_filter}",
        )
        logger.info(f"Admin {session.get('school_id')} viewed audit logs")
        return jsonify({"success": True, "audit_logs": audit_logs_data})

    except Exception as e:
        logger.error(f"Failed to get audit logs: {str(e)}")
        return jsonify({"error": "Failed to retrieve audit logs"}), 500
