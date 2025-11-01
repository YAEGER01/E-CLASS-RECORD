import logging
from flask import Blueprint, request, jsonify, session
from utils.auth_utils import login_required
from utils.db_conn import get_db_connection
from utils.live import emit_live_version_update

logger = logging.getLogger(__name__)

student_bp = Blueprint("student", __name__)


@student_bp.route("/api/student/join-class", methods=["POST"], endpoint="join_class")
@login_required
def join_class():
    if session.get("role") != "student":
        return jsonify({"error": "Access denied. Student privileges required."}), 403

    try:
        with get_db_connection().cursor() as cursor:
            cursor.execute(
                "SELECT id FROM students WHERE user_id = %s", (session["user_id"],)
            )
            student = cursor.fetchone()
            if not student:
                return jsonify({"error": "Student profile not found"}), 404

            data = request.get_json()
            join_code = (data.get("join_code", "") or "").strip().upper()
            if not join_code:
                return jsonify({"error": "Join code is required"}), 400
            if len(join_code) != 6:
                return jsonify({"error": "Join code must be 6 characters"}), 400

            cursor.execute("SELECT * FROM classes WHERE join_code = %s", (join_code,))
            class_obj = cursor.fetchone()
            if not class_obj:
                return jsonify({"error": "Invalid join code. Class not found."}), 404

            cursor.execute(
                "SELECT id FROM student_classes WHERE student_id = %s AND class_id = %s",
                (student["id"], class_obj["id"]),
            )
            existing = cursor.fetchone()
            if existing:
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
                return (
                    jsonify(
                        {
                            "error": "You are already enrolled in this class",
                            "already_enrolled": True,
                            "class_info": {
                                "class_id": computed_class_id,
                                "course": class_obj["course"],
                                "section": class_obj["section"],
                                "schedule": class_obj["schedule"],
                            },
                        }
                    ),
                    400,
                )

            cursor.execute(
                "INSERT INTO student_classes (student_id, class_id) VALUES (%s, %s)",
                (student["id"], class_obj["id"]),
            )
            get_db_connection().commit()

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
            try:
                emit_live_version_update(int(class_obj["id"]))
            except Exception as _e:
                logger.warning(f"Emit after join class failed: {_e}")

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


@student_bp.route(
    "/api/student/joined-classes", methods=["GET"], endpoint="get_joined_classes"
)
@login_required
def get_joined_classes():
    if session.get("role") != "student":
        return jsonify({"error": "Access denied. Student privileges required."}), 403

    try:
        with get_db_connection().cursor() as cursor:
            cursor.execute(
                "SELECT id FROM students WHERE user_id = %s", (session["user_id"],)
            )
            student = cursor.fetchone()
            if not student:
                return jsonify({"error": "Student profile not found"}), 404

            cursor.execute(
                """SELECT c.*, sc.joined_at FROM classes c
                JOIN student_classes sc ON c.id = sc.class_id
                WHERE sc.student_id = %s""",
                (student["id"],),
            )
            enrollments = cursor.fetchall()

            classes_data = []
            for enrollment in enrollments:
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
                        "instructor_name": "Instructor",
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


@student_bp.route(
    "/api/student/leave-class/<int:class_id>",
    methods=["DELETE"],
    endpoint="leave_class",
)
@login_required
def leave_class(class_id):
    if session.get("role") != "student":
        return jsonify({"error": "Access denied. Student privileges required."}), 403

    try:
        with get_db_connection().cursor() as cursor:
            cursor.execute(
                "SELECT id FROM students WHERE user_id = %s", (session["user_id"],)
            )
            student = cursor.fetchone()
            if not student:
                return jsonify({"error": "Student profile not found"}), 404

            cursor.execute(
                "SELECT id FROM student_classes WHERE student_id = %s AND class_id = %s",
                (student["id"], class_id),
            )
            enrollment = cursor.fetchone()
            if not enrollment:
                return jsonify({"error": "You are not enrolled in this class"}), 400

            cursor.execute(
                "SELECT year, semester, course, section FROM classes WHERE id = %s",
                (class_id,),
            )
            class_obj = cursor.fetchone()

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
                class_obj["class_id"] = (
                    f"{formatted_year}-{formatted_semester} {class_obj['course']} {class_obj['section']}"
                )

            cursor.execute(
                "DELETE FROM student_classes WHERE student_id = %s AND class_id = %s",
                (student["id"], class_id),
            )

            cursor.execute(
                "SELECT id FROM student_classes WHERE student_id = %s AND class_id = %s",
                (student["id"], class_id),
            )
            remaining = cursor.fetchone()
            if remaining:
                logger.error(
                    f"Failed to delete enrollment for student {student['id']} and class {class_id}"
                )
                return (
                    jsonify({"error": "Failed to leave class - please try again"}),
                    500,
                )

        get_db_connection().commit()

        try:
            emit_live_version_update(int(class_id))
        except Exception as _e:
            logger.warning(f"Emit after leave class failed: {_e}")

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
