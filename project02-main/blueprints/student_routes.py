import logging
import os
import uuid
from flask import Blueprint, jsonify, render_template, request, session, url_for
from werkzeug.utils import secure_filename
from utils.auth_utils import login_required
from utils.db_conn import get_db_connection
from utils.live import emit_live_version_update

logger = logging.getLogger(__name__)

student_bp = Blueprint("student", __name__)


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
                try:
                    # Safely coerce year/semester to strings; handle None or unexpected types
                    year_raw = (
                        enrollment.get("year") if isinstance(enrollment, dict) else None
                    )
                    year_str = str(year_raw) if year_raw is not None else ""
                    formatted_year = year_str[-2:] if year_str else "XX"

                    sem_raw = (
                        enrollment.get("semester")
                        if isinstance(enrollment, dict)
                        else None
                    )
                    sem_str = str(sem_raw).lower() if sem_raw is not None else ""
                    if "1st" in sem_str:
                        formatted_semester = "1"
                    elif "2nd" in sem_str:
                        formatted_semester = "2"
                    else:
                        formatted_semester = "1"

                    computed_class_id = f"{formatted_year}-{formatted_semester} {enrollment.get('course')} {enrollment.get('section')}"

                    joined_at_val = enrollment.get("joined_at")
                    joined_at_iso = None
                    try:
                        if joined_at_val:
                            joined_at_iso = joined_at_val.isoformat()
                    except Exception:
                        try:
                            joined_at_iso = str(joined_at_val)
                        except Exception:
                            joined_at_iso = None

                    classes_data.append(
                        {
                            "id": enrollment.get("id"),
                            "class_id": computed_class_id,
                            "year": enrollment.get("year"),
                            "semester": enrollment.get("semester"),
                            "course": enrollment.get("course"),
                            "track": enrollment.get("track"),
                            "section": enrollment.get("section"),
                            "schedule": enrollment.get("schedule"),
                            "class_code": enrollment.get("class_code"),
                            "join_code": enrollment.get("join_code"),
                            "instructor_name": "Instructor",
                            "joined_at": joined_at_iso,
                        }
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to process enrollment record %s: %s", enrollment, e
                    )
                    # Skip problematic enrollment but continue
                    continue

        logger.info(
            f"Retrieved {len(classes_data)} joined classes for student {session.get('school_id')}"
        )
        return jsonify({"classes": classes_data})
    except Exception as e:
        logger.error(f"Failed to get joined classes: {str(e)}")
        return jsonify({"error": "Failed to retrieve joined classes"}), 500


@student_bp.route("/api/student/join-class", methods=["POST"], endpoint="join_class")
@login_required
def join_class():
    """Join a class using join code."""
    if session.get("role") != "student":
        return jsonify({"error": "Access denied. Student privileges required."}), 403
    conn = None
    try:
        data = request.get_json() or {}
        join_code = (data.get("join_code") or "").strip().upper()

        logger.info(
            f"join_class called with join_code: '{join_code}' for user_id={session.get('user_id')}')"
        )

        if not join_code:
            return jsonify({"error": "Join code is required"}), 400

        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Get student id
            cursor.execute(
                "SELECT id FROM students WHERE user_id = %s", (session["user_id"],)
            )
            student = cursor.fetchone()
            if not student:
                logger.warning(
                    "join_class: student profile not found for user_id=%s",
                    session.get("user_id"),
                )
                return jsonify({"error": "Student profile not found"}), 404

            # Find class by join code
            cursor.execute(
                "SELECT * FROM classes WHERE UPPER(join_code) = %s", (join_code,)
            )
            class_obj = cursor.fetchone()
            if not class_obj:
                logger.info("join_class: no class found for join_code '%s'", join_code)
                return jsonify({"error": "Invalid join code. Class not found."}), 404

            # Check existing enrollment
            cursor.execute(
                "SELECT id FROM student_classes WHERE student_id = %s AND class_id = %s",
                (student["id"], class_obj["id"]),
            )
            existing = cursor.fetchone()
            if existing:
                logger.info(
                    "join_class: student %s already enrolled in class %s",
                    student["id"],
                    class_obj["id"],
                )
                return jsonify({"error": "You are already enrolled in this class"}), 400

            # Insert enrollment
            cursor.execute(
                "INSERT INTO student_classes (student_id, class_id, joined_at) VALUES (%s, %s, NOW())",
                (student["id"], class_obj["id"]),
            )
        conn.commit()

        try:
            emit_live_version_update(int(class_obj["id"]))
        except Exception as _e:
            logger.warning(f"Emit after join class failed: {_e}")

        logger.info(
            f"Student {session.get('school_id')} joined class: {class_obj.get('class_code') or class_obj.get('id')}"
        )

        return jsonify(
            {
                "success": True,
                "message": f"Successfully joined class: {class_obj.get('class_code') or class_obj.get('id')}",
                "class": {
                    "id": class_obj.get("id"),
                    "class_id": class_obj.get("class_code") or class_obj.get("id"),
                    "course": class_obj.get("course"),
                    "section": class_obj.get("section"),
                    "schedule": class_obj.get("schedule"),
                },
            }
        )
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        logger.error(
            f"Failed to join class for student {session.get('school_id')}: {str(e)}"
        )
        return jsonify({"error": "Failed to join class"}), 500


@student_bp.route(
    "/student/classes/<int:class_id>/grades",
    methods=["GET"],
    endpoint="student_class_grades",
)
@login_required
def student_class_grades(class_id):
    if session.get("role") != "student":
        return "Access denied", 403
    return render_template("student_class_grades.html", class_id=class_id)


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


@student_bp.route(
    "/api/student/classes/<int:class_id>/grades",
    methods=["GET"],
    endpoint="get_student_class_grades",
)
@login_required
def get_student_class_grades(class_id):
    if session.get("role") != "student":
        return jsonify({"error": "Access denied. Student privileges required."}), 403
    try:
        import json

        # Get student ID from database
        with get_db_connection().cursor() as cursor:
            cursor.execute(
                "SELECT id FROM students WHERE user_id = %s", (session["user_id"],)
            )
            student = cursor.fetchone()
            if not student:
                return jsonify({"error": "Student profile not found"}), 404
            student_id = student["id"]

            # Fetch latest grade snapshot from DB
            cursor.execute(
                "SELECT snapshot_json FROM grade_snapshots WHERE class_id = %s ORDER BY id DESC LIMIT 1",
                (class_id,),
            )
            snapshot_row = cursor.fetchone()
            if not snapshot_row:
                return (
                    jsonify(
                        {
                            "message": "No Snapshots",
                            "error": "No grade snapshots found for this class and student.",
                        }
                    ),
                    404,
                )
            snapshot = json.loads(snapshot_row["snapshot_json"])

            # Fetch class details
            cursor.execute(
                "SELECT course, section FROM classes WHERE id = %s", (class_id,)
            )
            class_row = cursor.fetchone()
            course = class_row["course"] if class_row else "Unknown Course"
            section = class_row["section"] if class_row else "Unknown Section"

            # Fetch grade structure
            cursor.execute(
                "SELECT structure_json FROM grade_structures WHERE class_id = %s AND is_active = 1",
                (class_id,),
            )
            structure_row = cursor.fetchone()
            structure_json = (
                json.loads(structure_row["structure_json"])
                if structure_row and structure_row["structure_json"]
                else {}
            )

        # Validate snapshot structure
        if not snapshot.get("students") or not snapshot.get("assessments"):
            return (
                jsonify(
                    {"message": "No Snapshots", "error": "Snapshot data incomplete."}
                ),
                404,
            )

        # Find student data
        student_data = None
        for s in snapshot["students"]:
            if str(s.get("student_id")) == str(student_id):
                student_data = s
                break
        if not student_data:
            return (
                jsonify(
                    {"message": "No Snapshots", "error": "Student snapshot not found"}
                ),
                404,
            )

        # Merge assessments into structure_json for display
        if structure_json and snapshot.get("assessments"):
            assessments = snapshot["assessments"]
            for category, subcats in structure_json.items():
                for subcat in subcats:
                    subcat["assessments"] = [
                        {
                            "id": a["id"],
                            "name": a["name"],
                            "max_score": a["max_score"],
                            "released_score": score,
                            "color": (
                                "red"
                                if score is not None and score < a["max_score"] / 3
                                else (
                                    "yellow"
                                    if score is not None
                                    and score < 2 * a["max_score"] / 3
                                    else "green" if score is not None else "gray"
                                )
                            ),
                        }
                        for a in assessments
                        if a["category"] == category
                        and a["subcategory"] == subcat["name"]
                        for score in [
                            next(
                                (
                                    s["score"]
                                    for s in student_data.get("scores", [])
                                    if s["assessment_id"] == a["id"]
                                ),
                                None,
                            )
                        ]
                    ]

        # Get final grade and equivalent
        computed = student_data.get("computed", {})
        final_grade = computed.get("final_grade")
        equivalent = computed.get("letter_grade")

        # Compose details for frontend
        details = {
            "scores": student_data.get("scores", []),
            "structure_json": structure_json,
        }
        return jsonify(
            {
                "class_id": snapshot.get("meta", {}).get("class_id"),
                "course": course,
                "section": section,
                "final_grade": final_grade,
                "equivalent": equivalent,
                "details": details,
            }
        )
    except Exception as e:
        logger.error(f"Failed to get student grades: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to retrieve grades"}), 500


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


# Student Classes Table Page
@student_bp.route("/student/classes", methods=["GET"], endpoint="student_classes")
@login_required
def student_classes():
    if session.get("role") != "student":
        return "Access denied", 403
    try:
        with get_db_connection().cursor() as cursor:
            # Get student info
            cursor.execute(
                "SELECT * FROM students WHERE user_id = %s", (session.get("user_id"),)
            )
            student = cursor.fetchone()
            if not student:
                logger.error(
                    "Student profile not found for user_id %s", session.get("user_id")
                )
                return "Student profile not found", 404

            # Get personal info (fallback to empty dict if missing)
            personal = {}
            try:
                cursor.execute(
                    "SELECT * FROM personal_info WHERE id = %s",
                    (student.get("personal_info_id"),),
                )
                personal = cursor.fetchone() or {}
            except Exception as e:
                logger.warning(f"Personal info fetch failed: {e}")

            # Get joined classes
            cursor.execute(
                """
                SELECT c.*, sc.joined_at
                FROM classes c
                JOIN student_classes sc ON c.id = sc.class_id
                WHERE sc.student_id = %s
            """,
                (student.get("id"),),
            )
            enrollments = cursor.fetchall() or []
            classes = []
            for cls in enrollments:
                # Get instructor info (fallback to Unknown)
                instructor_name = "Unknown"
                try:
                    cursor.execute(
                        "SELECT * FROM instructors WHERE id = %s",
                        (cls.get("instructor_id"),),
                    )
                    instructor = cursor.fetchone()
                    if instructor:
                        cursor.execute(
                            "SELECT * FROM personal_info WHERE id = %s",
                            (instructor.get("personal_info_id"),),
                        )
                        instr_personal = cursor.fetchone()
                        if instr_personal:
                            instructor_name = f"{instr_personal.get('first_name','')} {instr_personal.get('last_name','')}"
                except Exception as e:
                    logger.warning(f"Instructor info fetch failed: {e}")

                # Get released grades for this student/class
                released_grade = None
                grade_data = None
                try:
                    cursor.execute(
                        "SELECT * FROM released_grades WHERE class_id = %s AND student_id = %s AND status = 'released'",
                        (cls.get("id"), student.get("id")),
                    )
                    released_grade = cursor.fetchone()
                    if released_grade and released_grade.get("grade_payload"):
                        import json

                        try:
                            grade_data = json.loads(released_grade["grade_payload"])
                        except Exception as e:
                            logger.warning(f"Grade payload JSON decode failed: {e}")
                            grade_data = None
                except Exception as e:
                    logger.warning(f"Released grades fetch failed: {e}")

                # If grade_data is present, recalculate using grade_calculation
                final_grade = None
                equivalent = None
                try:
                    if grade_data and "scores" in grade_data:
                        from utils.grade_calculation import (
                            perform_grade_computation,
                            get_equivalent,
                        )

                        # Normalize for computation
                        # Fetch structure for this class
                        cursor.execute(
                            "SELECT * FROM grade_structures WHERE class_id = %s AND is_active = 1",
                            (cls.get("id"),),
                        )
                        structure = cursor.fetchone()
                        structure_json = None
                        if structure and structure.get("structure_json"):
                            import json

                            try:
                                structure_json = json.loads(structure["structure_json"])
                            except Exception as e:
                                logger.warning(f"Structure JSON decode failed: {e}")
                                structure_json = None
                        # Prepare normalized_rows for computation
                        normalized_rows = []
                        if structure_json:
                            for category, subcats in structure_json.items():
                                for subcat in subcats:
                                    normalized_rows.append(
                                        {
                                            "category": category,
                                            "name": subcat.get("name"),
                                            "weight": subcat.get("weight"),
                                            "assessment": None,
                                            "max_score": None,
                                        }
                                    )
                        # Prepare student_scores_named
                        student_scores_named = []
                        for score in grade_data.get("scores", []):
                            # You may need to fetch assessment name from id
                            assessment_name = None
                            try:
                                cursor.execute(
                                    "SELECT name FROM grade_assessments WHERE id = %s",
                                    (score.get("assessment_id"),),
                                )
                                assessment = cursor.fetchone()
                                assessment_name = (
                                    assessment.get("name") if assessment else None
                                )
                            except Exception as e:
                                logger.warning(f"Assessment name fetch failed: {e}")
                            student_scores_named.append(
                                {
                                    "student_id": student.get("id"),
                                    "assessment_name": assessment_name,
                                    "score": score.get("score"),
                                }
                            )
                        # Use perform_grade_computation
                        computed_grades = perform_grade_computation(
                            structure_json or {}, normalized_rows, student_scores_named
                        )
                        if computed_grades:
                            final_grade = computed_grades[0].get("final_grade")
                            equivalent = computed_grades[0].get("equivalent")
                except Exception as e:
                    logger.warning(f"Grade computation failed: {e}")
                # Fallback to released_grades values
                if not final_grade and released_grade:
                    final_grade = released_grade.get("final_grade")
                    equivalent = released_grade.get("equivalent")

                classes.append(
                    {
                        "id": cls.get("id"),
                        "code": cls.get("class_code") or cls.get("join_code"),
                        "name": cls.get("course"),
                        "subject": cls.get("subject"),
                        "instructor": instructor_name,
                        "final_grade": final_grade,
                        "equivalent": equivalent,
                    }
                )
        return render_template(
            "student_classes.html", classes=classes, student=student, personal=personal
        )
    except Exception as e:
        logger.error(f"Failed to load student classes page: {str(e)}", exc_info=True)
        return "Failed to load classes", 500


@student_bp.route(
    "/api/student/analytics", methods=["GET"], endpoint="student_analytics"
)
@login_required
def student_analytics():
    """Get basic analytics data for student dashboard (missing assessments, notifications)."""
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
            student_id = student["id"]

            # Get joined classes
            cursor.execute(
                """SELECT c.id, c.class_code, c.course, c.section, c.year, c.semester
                FROM classes c
                JOIN student_classes sc ON c.id = sc.class_id
                WHERE sc.student_id = %s""",
                (student_id,),
            )
            classes_data = cursor.fetchall()

            classes = []
            for cls in classes_data:
                # Get missing assessments for this class
                missing_assessments = []
                try:
                    # Get grade structure for this class
                    cursor.execute(
                        "SELECT structure_json FROM grade_structures WHERE class_id = %s AND is_active = 1",
                        (cls["id"],),
                    )
                    structure_row = cursor.fetchone()

                    if structure_row and structure_row["structure_json"]:
                        import json

                        structure = json.loads(structure_row["structure_json"])

                        # Get all assessments for this class with category and subcategory info
                        # grade_assessments does not store class_id directly; we join through
                        # grade_subcategories -> grade_categories -> grade_structures (by class_id)
                        cursor.execute(
                            """
                            SELECT ga.id, ga.name, gc.name as category, gsc.name as subcategory
                            FROM grade_assessments ga
                            JOIN grade_subcategories gsc ON ga.subcategory_id = gsc.id
                            JOIN grade_categories gc ON gsc.category_id = gc.id
                            JOIN grade_structures gs ON gc.structure_id = gs.id
                            WHERE gs.class_id = %s AND gs.is_active = 1
                            """,
                            (cls["id"],),
                        )
                        assessments = cursor.fetchall()

                        # Check which assessments the student hasn't completed
                        for assessment in assessments:
                            # Check if student has a score for this assessment
                            cursor.execute(
                                "SELECT score FROM student_scores WHERE student_id = %s AND assessment_id = %s",
                                (student_id, assessment["id"]),
                            )
                            score_row = cursor.fetchone()

                            # If no score found, it's missing
                            if not score_row or score_row["score"] is None:
                                missing_assessments.append(assessment["name"])

                except Exception as e:
                    logger.warning(
                        f"Failed to get missing assessments for class {cls['id']}: {e}"
                    )
                    missing_assessments = []

                # Format class name
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
                class_name = f"{formatted_year}-{formatted_semester} {cls['course']} {cls['section']}"

                # Get released grades for this class
                released_grades = []
                try:
                    cursor.execute(
                        "SELECT final_grade, equivalent, released_at FROM released_grades WHERE class_id = %s AND student_id = %s AND status = 'released'",
                        (cls["id"], student_id),
                    )
                    released_rows = cursor.fetchall()
                    for row in released_rows:
                        released_grades.append(
                            {
                                "final_grade": row["final_grade"],
                                "equivalent": row["equivalent"],
                                "released_at": (
                                    row["released_at"].isoformat()
                                    if row["released_at"]
                                    else None
                                ),
                            }
                        )
                except Exception as e:
                    logger.warning(
                        f"Failed to get released grades for class {cls['id']}: {e}"
                    )
                    released_grades = []

                classes.append(
                    {
                        "class_id": class_name,
                        "class_name": class_name,
                        "missing_assessments": missing_assessments,
                        "released_grades": released_grades,
                    }
                )

        return jsonify({"classes": classes})

    except Exception as e:
        logger.error(f"Failed to get student analytics: {str(e)}")
        return jsonify({"error": "Failed to retrieve analytics"}), 500
