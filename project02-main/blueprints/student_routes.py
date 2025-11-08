import logging
import os
import uuid
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, session, url_for, current_app
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


@student_bp.route("/api/student/profile", methods=["PUT"], endpoint="update_profile")
@login_required
def update_profile():
    """Update student personal info and profile files.

    Accepts multipart/form-data fields for personal info and files:
    - first_name, last_name, middle_name, email, phone, address, birth_date, gender,
      emergency_contact_name, emergency_contact_phone
    - course, year_level, section, track
    - face_photo, id_front, id_back (files)

    Returns JSON with updated profile and URLs for uploaded files.
    """
    if session.get("role") != "student":
        return (
            jsonify({"error": "Access denied. Student privileges required."}),
            403,
        )

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, personal_info_id FROM students WHERE user_id = %s",
                (session["user_id"],),
            )
            student = cursor.fetchone()
            if not student:
                return jsonify({"error": "Student profile not found"}), 404

            # Helper to store uploaded file under static/uploads and return relative path
            def save_upload(f):
                if not f:
                    return None
                uploads_root = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)), "static", "uploads"
                )
                os.makedirs(uploads_root, exist_ok=True)
                filename = secure_filename(f.filename)
                if not filename:
                    filename = f"{uuid.uuid4().hex}.bin"
                else:
                    # prefix with uuid to avoid collisions
                    filename = f"{uuid.uuid4().hex}_{filename}"
                dest = os.path.join(uploads_root, filename)
                f.save(dest)
                # return web-accessible path relative to static folder
                return f"uploads/{filename}"

            # Read form fields
            form = request.form
            files = request.files
            logger.debug(
                "update_profile called - form keys: %s, file keys: %s",
                list(form.keys()),
                list(files.keys()),
            )

            # Personal info fields
            pi_fields = {
                "first_name": form.get("first_name"),
                "last_name": form.get("last_name"),
                "middle_name": form.get("middle_name"),
                "email": form.get("email"),
                "phone": form.get("phone"),
                "address": form.get("address"),
                "birth_date": form.get("birth_date"),
                "gender": form.get("gender"),
                "emergency_contact_name": form.get("emergency_contact_name"),
                "emergency_contact_phone": form.get("emergency_contact_phone"),
            }

            # Normalize certain fields: convert empty strings to None to avoid DB errors
            # (MySQL rejects empty string for DATE columns). Keep other empty strings as-is.
            for k in ("birth_date",):
                if k in pi_fields and pi_fields[k] == "":
                    pi_fields[k] = None

            # Student profile fields
            student_updates = {
                "course": form.get("course"),
                "year_level": form.get("year_level"),
                "section": form.get("section"),
                "track": form.get("track"),
            }

            # Normalize numeric/optional fields: convert empty strings to None and
            # coerce year_level to integer when provided
            if "year_level" in student_updates:
                yl = student_updates.get("year_level")
                if yl is None or (isinstance(yl, str) and yl.strip() == ""):
                    student_updates["year_level"] = None
                else:
                    try:
                        student_updates["year_level"] = int(str(yl).strip())
                    except Exception:
                        # invalid value -> skip updating year_level
                        student_updates["year_level"] = None

            # Handle file uploads
            face_path = (
                save_upload(files.get("face_photo")) if "face_photo" in files else None
            )
            id_front_path = (
                save_upload(files.get("id_front")) if "id_front" in files else None
            )
            id_back_path = (
                save_upload(files.get("id_back")) if "id_back" in files else None
            )

            # Update or insert personal_info
            pi_id = student.get("personal_info_id")
            if pi_id:
                # build SET clause
                set_parts = []
                params = []
                for k, v in pi_fields.items():
                    if v is not None:
                        set_parts.append(f"{k} = %s")
                        params.append(v)
                if set_parts:
                    params.append(pi_id)
                    sql = (
                        f"UPDATE personal_info SET {', '.join(set_parts)} WHERE id = %s"
                    )
                    cursor.execute(sql, tuple(params))
            else:
                # Only insert if we have at least a name or email
                if (
                    pi_fields.get("first_name")
                    or pi_fields.get("last_name")
                    or pi_fields.get("email")
                ):
                    cols = []
                    vals = []
                    params = []
                    for k, v in pi_fields.items():
                        if v is not None:
                            cols.append(k)
                            vals.append("%s")
                            params.append(v)
                    if cols:
                        sql = f"INSERT INTO personal_info ({', '.join(cols)}) VALUES ({', '.join(vals)})"
                        cursor.execute(sql, tuple(params))
                        pi_id = cursor.lastrowid
                        cursor.execute(
                            "UPDATE students SET personal_info_id = %s WHERE id = %s",
                            (pi_id, student["id"]),
                        )

            # Update students table for profile fields and file paths
            stu_set = []
            stu_params = []
            for k, v in student_updates.items():
                if v is not None:
                    stu_set.append(f"{k} = %s")
                    stu_params.append(v)
            if id_front_path:
                stu_set.append("id_front_path = %s")
                stu_params.append(id_front_path)
            if id_back_path:
                stu_set.append("id_back_path = %s")
                stu_params.append(id_back_path)
            if face_path:
                stu_set.append("face_photo_path = %s")
                stu_params.append(face_path)

            if stu_set:
                stu_params.append(student["id"])
                sql = f"UPDATE students SET {', '.join(stu_set)} WHERE id = %s"
                cursor.execute(sql, tuple(stu_params))

        conn.commit()

        # Build response profile
        profile = {}
        # Fetch updated student + personal_info to include in response
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT s.*, pi.first_name, pi.last_name, pi.middle_name, pi.email, pi.phone, pi.address, pi.birth_date, pi.gender, pi.emergency_contact_name, pi.emergency_contact_phone FROM students s LEFT JOIN personal_info pi ON s.personal_info_id = pi.id WHERE s.user_id = %s",
                (session["user_id"],),
            )
            row = cursor.fetchone()
            if row:
                profile.update(row)

        # Convert file paths to static URLs
        def static_url_for(path):
            if not path:
                return None
            return url_for("static", filename=path)

        result = {
            "success": True,
            "message": "Profile updated",
            "profile": {
                "course": profile.get("course"),
                "year_level": profile.get("year_level"),
                "section": profile.get("section"),
                "track": profile.get("track"),
                "photo_url": static_url_for(profile.get("face_photo_path")),
                "face_photo_url": static_url_for(profile.get("face_photo_path")),
                "id_front_url": static_url_for(profile.get("id_front_path")),
                "id_back_url": static_url_for(profile.get("id_back_path")),
                "personal_info": {
                    "first_name": profile.get("first_name"),
                    "last_name": profile.get("last_name"),
                    "middle_name": profile.get("middle_name"),
                    "email": profile.get("email"),
                    "phone": profile.get("phone"),
                    "address": profile.get("address"),
                    "birth_date": profile.get("birth_date"),
                    "gender": profile.get("gender"),
                    "emergency_contact_name": profile.get("emergency_contact_name"),
                    "emergency_contact_phone": profile.get("emergency_contact_phone"),
                },
            },
        }

        logger.info(f"Student profile updated for {session.get('school_id')}")
        return jsonify(result)
    except Exception as e:
        conn.rollback()
        logger.exception(
            "Failed updating profile for %s: %s", session.get("school_id"), e
        )
        # Return error detail to help debugging in development
        return jsonify({"error": "Failed to update profile", "detail": str(e)}), 500
    finally:
        try:
            conn.close()
        except Exception:
            pass
