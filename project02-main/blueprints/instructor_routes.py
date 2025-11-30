import logging
import json
from datetime import datetime
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    jsonify,
)
from utils.auth_utils import login_required
from utils.db_conn import get_db_connection
from utils.live import (
    emit_live_version_update,
    get_cached_class_live_version,
    _cache_get,
    _cache_put,
    _grouped_cache_get,
    _grouped_cache_put,
)
from flask_wtf.csrf import generate_csrf

logger = logging.getLogger(__name__)

instructor_bp = Blueprint("instructor", __name__)


# Update max_score for an assessment
@instructor_bp.route("/assessments/<int:assessment_id>/update_max", methods=["POST"])
@login_required
def api_update_assessment_max_score(assessment_id):
    """Update the max_score of an assessment by ID."""

    instructor_id, err = _require_instructor()
    if err:
        return err
    try:
        data = request.get_json(silent=True) or {}
        max_score = data.get("max_score")
        if max_score is None:
            return jsonify({"error": "max_score_required"}), 400
        try:
            max_score = float(max_score)
        except Exception:
            return jsonify({"error": "invalid_max_score"}), 400
        if max_score <= 0:
            return jsonify({"error": "max_score_must_be_positive"}), 400

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Get subcategory and class for this assessment
                cursor.execute(
                    """
                    SELECT ga.subcategory_id, gsc.category_id, gc.structure_id, gs.class_id
                    FROM grade_assessments ga
                    JOIN grade_subcategories gsc ON ga.subcategory_id = gsc.id
                    JOIN grade_categories gc ON gsc.category_id = gc.id
                    JOIN grade_structures gs ON gc.structure_id = gs.id
                    WHERE ga.id = %s
                    """,
                    (assessment_id,),
                )
                row = cursor.fetchone()
                if not row:
                    return jsonify({"error": "assessment_not_found"}), 404
                class_id = row["class_id"] if isinstance(row, dict) else row[3]
                # Check instructor owns this class
                if not _instructor_owns_class(class_id, session.get("user_id")):
                    return jsonify({"error": "forbidden"}), 403

                # Update max_score
                cursor.execute(
                    "UPDATE grade_assessments SET max_score = %s WHERE id = %s",
                    (max_score, assessment_id),
                )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        return (
            jsonify(
                {
                    "success": True,
                    "assessment_id": assessment_id,
                    "max_score": max_score,
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Failed to update assessment max_score: {str(e)}")
        return jsonify({"error": "failed_to_update"}), 500


from utils.db_conn import get_db_connection
from utils.live import (
    emit_live_version_update,
    get_cached_class_live_version,
    _cache_get,
    _cache_put,
    _grouped_cache_get,
    _grouped_cache_put,
)
from flask_wtf.csrf import generate_csrf

logger = logging.getLogger(__name__)


# Local helpers to avoid circular imports
def _require_instructor():
    if "user_id" not in session:
        return None, (jsonify({"error": "not_logged_in"}), 401)
    if session.get("role") != "instructor":
        return None, (jsonify({"error": "forbidden"}), 403)
    instructor_id = session.get("instructor_id")
    if not instructor_id:
        try:
            with get_db_connection().cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM instructors WHERE user_id = %s",
                    (session.get("user_id"),),
                )
                r = cursor.fetchone()
                if not r:
                    return None, (jsonify({"error": "instructor_not_found"}), 404)
                instructor_id = r["id"]
                session["instructor_id"] = instructor_id
        except Exception:
            return None, (jsonify({"error": "instructor_lookup_failed"}), 500)
    return instructor_id, None


def _instructor_owns_class(class_id: int, user_id: int) -> bool:
    try:
        with get_db_connection().cursor() as cursor:
            # Try to return the latest draft snapshot (normalized) if available
            try:
                cursor.execute(
                    "SELECT snapshot_json, version, created_at FROM grade_snapshots "
                    "WHERE class_id = %s AND status = 'draft' ORDER BY version DESC LIMIT 1",
                    (class_id,),
                )
                sr = cursor.fetchone()
                if sr:
                    raw = sr.get("snapshot_json")
                    normalized = _normalize_snapshot(raw)
                    # fetch student metadata for display
                    sids = [
                        s.get("student_id")
                        for s in normalized.get("students", [])
                        if s.get("student_id")
                    ]
                    rows = {}
                    if sids:
                        placeholders = ",".join(["%s"] * len(sids))
                        params = [class_id] + sids
                        cursor.execute(
                            f"""
                            SELECT s.id AS student_id,
                                   u.school_id,
                                   pi.first_name,
                                   pi.last_name,
                                   pi.middle_name,
                                   rg.status,
                                   rg.released_at
                            FROM students s
                            JOIN users u ON s.user_id = u.id
                            LEFT JOIN personal_info pi ON s.personal_info_id = pi.id
                            LEFT JOIN released_grades rg
                                ON rg.student_id = s.id AND rg.class_id = %s
                            WHERE s.id IN ({placeholders})
                            """,
                            params,
                        )
                        rows = {r["student_id"]: r for r in (cursor.fetchall() or [])}

                    out_students = []
                    for s in normalized.get("students", []):
                        sid = s.get("student_id")
                        meta = rows.get(sid) if rows else None
                        if meta:
                            fn = meta.get("first_name") or ""
                            ln = meta.get("last_name") or ""
                            mn = meta.get("middle_name") or ""
                            name = (
                                f"{ln}, {fn} {mn}".strip()
                                if fn and ln
                                else meta.get("school_id") or f"Student {sid}"
                            )
                            status_val = (meta.get("status") or "").lower()
                            is_released = status_val == "released"
                            released_raw = meta.get("released_at")
                            if is_released and isinstance(released_raw, datetime):
                                released_date = released_raw.strftime("%Y-%m-%d")
                            elif is_released and released_raw:
                                released_date = str(released_raw)
                            else:
                                released_date = None
                        else:
                            name = None
                            is_released = False
                            released_date = None

                        out_students.append(
                            {
                                "id": sid,
                                "name": name,
                                "school_id": meta.get("school_id") if meta else None,
                                "final_grade": s.get("final_grade"),
                                "equivalent": s.get("equivalent"),
                                "is_released": is_released,
                                "released_date": released_date,
                                "scores": s.get("scores", []),
                            }
                        )

                    return jsonify(
                        {
                            "class_id": class_id,
                            "snapshot": {
                                "version": sr.get("version"),
                                "created_at": sr.get("created_at"),
                                "assessments": normalized.get("assessments"),
                                "students": out_students,
                            },
                            "total_students": len(out_students),
                        }
                    )
            except Exception:
                # If snapshot path fails, fall back to the enrolled-students path below
                pass
            cursor.execute("SELECT id FROM instructors WHERE user_id = %s", (user_id,))
            instr = cursor.fetchone()
            if not instr:
                return False
            cursor.execute(
                "SELECT id FROM classes WHERE id = %s AND instructor_id = %s",
                (class_id, instr["id"]),
            )
            return cursor.fetchone() is not None
    except Exception:
        return False


def _generate_class_codes():
    import uuid, hashlib, random

    class_code = str(uuid.uuid4())
    hash_obj = hashlib.md5(class_code.encode())
    hash_hex = hash_obj.hexdigest()
    join_code = "".join(c for c in hash_hex[:6] if c.isdigit())
    while len(join_code) < 6:
        join_code += str(random.randint(0, 9))
    return class_code, join_code[:6]


@instructor_bp.route(
    "/api/assessments/simple", methods=["POST"], endpoint="api_create_assessment_simple"
)
@login_required
def api_create_assessment_simple():
    """Create an assessment under a given subcategory by ID.
    Expects form-urlencoded: name, subcategory_id, max_score.
    """

    instructor_id, err = _require_instructor()
    if err:
        return err

    # Accept form-encoded or JSON; allow camelCase fallbacks
    json_payload = request.get_json(silent=True) or {}
    try:
        form_payload = request.form.to_dict(flat=True)
    except Exception:
        form_payload = {}
    data = {**json_payload, **form_payload}

    name = (data.get("name") or "").strip()
    subcategory_id = data.get("subcategory_id") or data.get("subcategoryId")
    max_score = data.get("max_score") or data.get("maxScore")

    if not name:
        return jsonify({"error": "name_required"}), 400
    try:
        subcategory_id = int(subcategory_id)
    except Exception:
        return (
            jsonify(
                {
                    "error": "invalid_parameters",
                    "details": "subcategory_id must be integer",
                    "received": str(subcategory_id),
                }
            ),
            400,
        )
    try:
        max_score = float(max_score)
    except Exception:
        return (
            jsonify(
                {
                    "error": "invalid_parameters",
                    "details": "max_score must be number",
                    "received": str(max_score),
                }
            ),
            400,
        )
    if max_score <= 0:
        return jsonify({"error": "max_score_must_be_positive"}), 400

    try:
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Verify subcategory belongs to a class owned by this instructor
                cursor.execute(
                    """
                    SELECT c.id AS class_id, gs.id AS structure_id
                    FROM grade_subcategories gsc
                    JOIN grade_categories gc ON gsc.category_id = gc.id
                    JOIN grade_structures gs ON gc.structure_id = gs.id
                    JOIN classes c ON gs.class_id = c.id
                    WHERE gsc.id = %s
                    """,
                    (subcategory_id,),
                )
                row = cursor.fetchone()
                if not row:
                    return jsonify({"error": "subcategory_not_found"}), 404
                class_id = row.get("class_id") if isinstance(row, dict) else row[0]

                # ownership check
                if not _instructor_owns_class(class_id, session.get("user_id")):
                    return jsonify({"error": "forbidden"}), 403

                # Next position within subcategory
                cursor.execute(
                    "SELECT COALESCE(MAX(position), 0) + 1 AS pos FROM grade_assessments WHERE subcategory_id = %s",
                    (subcategory_id,),
                )
                rpos = cursor.fetchone() or {}
                next_pos = (
                    rpos.get("pos")
                    if isinstance(rpos, dict)
                    else (rpos[0] if rpos else 1)
                )
                if not next_pos:
                    next_pos = 1

                cursor.execute(
                    """
                    INSERT INTO grade_assessments (subcategory_id, name, weight, max_score, position, created_at)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                    """,
                    (subcategory_id, name, None, max_score, next_pos),
                )
                new_id = getattr(cursor, "lastrowid", None)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        return (
            jsonify(
                {
                    "id": new_id,
                    "name": name,
                    "subcategory_id": subcategory_id,
                    "max_score": max_score,
                    "position": next_pos,
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Failed to create assessment: {str(e)}")
        return jsonify({"error": "failed_to_create"}), 500


@instructor_bp.route("/instructor/classes", endpoint="instructor_classes")
@login_required
def instructor_classes():
    if session.get("role") != "instructor":
        flash("Access denied. Instructor privileges required.", "error")
        return redirect(url_for("home"))
    logger.info(f"Instructor {session.get('school_id')} accessed class management")
    return render_template("instructor_classes.html")


@instructor_bp.route(
    "/api/instructor/classes", methods=["GET"], endpoint="get_instructor_classes"
)
@login_required
def get_instructor_classes():
    if session.get("role") != "instructor":
        return jsonify({"error": "Access denied"}), 403

    try:
        with get_db_connection().cursor() as cursor:
            cursor.execute(
                "SELECT id FROM instructors WHERE user_id = %s", (session["user_id"],)
            )
            instructor = cursor.fetchone()
            if not instructor:
                return jsonify({"error": "Instructor profile not found"}), 404

            cursor.execute(
                "SELECT * FROM classes WHERE instructor_id = %s", (instructor["id"],)
            )
            classes = cursor.fetchall()

            classes_data = []
            for cls in classes:
                cursor.execute(
                    "SELECT COUNT(*) as count FROM student_classes WHERE class_id = %s",
                    (cls["id"],),
                )
                member_count = cursor.fetchone()["count"]

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
                        "subject": (
                            cls.get("subject")
                            if isinstance(cls, dict)
                            else cls["subject"]
                        ),
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


@instructor_bp.route(
    "/api/instructor/classes", methods=["POST"], endpoint="create_class"
)
@login_required
def create_class():
    if session.get("role") != "instructor":
        return jsonify({"error": "Access denied"}), 403

    conn = None
    try:
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM instructors WHERE user_id = %s",
                    (session["user_id"],),
                )
                instructor = cursor.fetchone()
                if not instructor:
                    return jsonify({"error": "Instructor profile not found"}), 404

                data = request.get_json()
                required_fields = [
                    "classType",
                    "year",
                    "semester",
                    "course",
                    "subject",
                    "track",
                    "section",
                    "schedule",
                ]
                for field in required_fields:
                    if not data.get(field):
                        return jsonify({"error": f"{field} is required"}), 400

                if data.get("classType") not in ["MINOR", "MAJOR"]:
                    return (
                        jsonify({"error": "classType must be either MINOR or MAJOR"}),
                        400,
                    )

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

                class_code, join_code = _generate_class_codes()
                cursor.execute(
                    "SELECT id FROM classes WHERE join_code = %s", (join_code,)
                )
                while cursor.fetchone():
                    class_code, join_code = _generate_class_codes()
                    cursor.execute(
                        "SELECT id FROM classes WHERE join_code = %s", (join_code,)
                    )

                cursor.execute(
                    """INSERT INTO classes
                    (instructor_id, class_type, year, semester, course, subject, track, section, schedule, class_code, join_code)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (
                        instructor["id"],
                        data["classType"],
                        data["year"],
                        data["semester"],
                        data["course"],
                        data.get("subject"),
                        data["track"],
                        section,
                        data["schedule"],
                        class_code,
                        join_code,
                    ),
                )

                class_id = cursor.lastrowid
            conn.commit()
        except Exception:
            conn.rollback()
            raise

            year_str = str(data["year"]) if data["year"] else ""
            formatted_year = year_str[-2:] if year_str else "XX"
            semester_str = str(data["semester"]) if data["semester"] else ""
            formatted_semester = (
                "1"
                if semester_str and "1st" in semester_str.lower()
                else ("2" if semester_str and "2nd" in semester_str.lower() else "1")
            )
            computed_class_id = (
                f"{formatted_year}-{formatted_semester} {data['course']} {section}"
            )

            logger.info(
                f"Instructor {session.get('school_id')} created class: {computed_class_id}"
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
                        "subject": data.get("subject"),
                        "track": data["track"],
                        "section": section,
                        "schedule": data["schedule"],
                        "class_id": computed_class_id,
                        "class_code": class_code,
                        "join_code": join_code,
                    },
                }
            )
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(
            f"Failed to create class for instructor {session.get('school_id')}: {str(e)}"
        )
        return jsonify({"error": "Failed to create class"}), 500


@instructor_bp.route(
    "/api/instructor/classes/<int:class_id>", methods=["PUT"], endpoint="update_class"
)
@login_required
def update_class(class_id):
    if session.get("role") != "instructor":
        return jsonify({"error": "Access denied"}), 403

    conn = None
    try:
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM instructors WHERE user_id = %s",
                    (session["user_id"],),
                )
                instructor = cursor.fetchone()
                if not instructor:
                    return jsonify({"error": "Instructor profile not found"}), 404

                cursor.execute(
                    "SELECT * FROM classes WHERE id = %s AND instructor_id = %s",
                    (class_id, instructor["id"]),
                )
                cls = cursor.fetchone()
                if not cls:
                    return jsonify({"error": "Class not found or access denied"}), 404

                data = request.get_json() or {}
                required_fields = [
                    "year",
                    "semester",
                    "course",
                    "subject",
                    "track",
                    "section",
                    "schedule",
                ]
                for field in required_fields:
                    if not data.get(field):
                        return jsonify({"error": f"{field} is required"}), 400

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

                cursor.execute(
                    """UPDATE classes SET class_type=%s, year=%s, semester=%s,
                    course=%s, subject=%s, track=%s, section=%s, schedule=%s, updated_at=NOW()
                    WHERE id = %s""",
                    (
                        data.get("classType") or cls.get("class_type"),
                        data["year"],
                        data["semester"],
                        data["course"],
                        data["subject"],
                        data["track"],
                        section,
                        data["schedule"],
                        class_id,
                    ),
                )
            conn.commit()
        except Exception:
            conn.rollback()
            raise

        # Build returned class object
        year_str = str(data["year"]) if data["year"] else ""
        formatted_year = year_str[-2:] if year_str else "XX"
        semester_str = str(data["semester"]) if data["semester"] else ""
        formatted_semester = (
            "1"
            if semester_str and "1st" in semester_str.lower()
            else ("2" if semester_str and "2nd" in semester_str.lower() else "1")
        )
        computed_class_id = (
            f"{formatted_year}-{formatted_semester} {data['course']} {section}"
        )

        logger.info(f"Instructor {session.get('school_id')} updated class {class_id}")
        return jsonify(
            {
                "success": True,
                "message": "Class updated successfully",
                "class": {
                    "id": class_id,
                    "classType": data.get("classType") or cls.get("class_type"),
                    "year": data["year"],
                    "semester": data["semester"],
                    "course": data["course"],
                    "subject": data["subject"],
                    "track": data["track"],
                    "section": section,
                    "schedule": data["schedule"],
                    "class_id": computed_class_id,
                    "class_code": cls.get("class_code"),
                    "join_code": cls.get("join_code"),
                },
            }
        )
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(
            f"Failed to update class {class_id} for instructor {session.get('school_id')}: {str(e)}"
        )
        return jsonify({"error": "Failed to update class"}), 500


@instructor_bp.route(
    "/api/instructor/classes/<int:class_id>",
    methods=["DELETE"],
    endpoint="delete_class",
)
@login_required
def delete_class(class_id):
    if session.get("role") != "instructor":
        return jsonify({"error": "Access denied"}), 403

    conn = None
    try:
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM instructors WHERE user_id = %s",
                    (session["user_id"],),
                )
                instructor = cursor.fetchone()
                if not instructor:
                    return jsonify({"error": "Instructor profile not found"}), 404

                cursor.execute(
                    "SELECT * FROM classes WHERE id = %s AND instructor_id = %s",
                    (class_id, instructor["id"]),
                )
                cls = cursor.fetchone()
                if not cls:
                    return jsonify({"error": "Class not found or access denied"}), 404

                cursor.execute("DELETE FROM classes WHERE id = %s", (class_id,))
            conn.commit()
        except Exception:
            conn.rollback()
            raise

            logger.info(
                f"Instructor {session.get('school_id')} deleted class {class_id}"
            )
            return jsonify({"message": "Class deleted successfully"}), 200
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(
            f"Failed to delete class {class_id} for instructor {session.get('school_id')}: {str(e)}"
        )
        return jsonify({"error": "Failed to delete class"}), 500


@instructor_bp.route(
    "/api/instructor/classes/<int:class_id>/members",
    methods=["GET"],
    endpoint="get_class_members",
)
@login_required
def get_class_members(class_id):
    if session.get("role") != "instructor":
        return jsonify({"error": "Access denied"}), 403

    try:
        with get_db_connection().cursor() as cursor:
            cursor.execute(
                "SELECT id FROM instructors WHERE user_id = %s", (session["user_id"],)
            )
            instructor = cursor.fetchone()
            if not instructor:
                return jsonify({"error": "Instructor profile not found"}), 404

            cursor.execute(
                "SELECT * FROM classes WHERE id = %s AND instructor_id = %s",
                (class_id, instructor["id"]),
            )
            class_obj = cursor.fetchone()
            if not class_obj:
                return jsonify({"error": "Class not found or access denied"}), 404

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
        class_info = {
            "id": class_obj["id"],
            "course": class_obj.get("course"),
            "subject": class_obj.get("subject"),
            "track": class_obj.get("track"),
            "section": class_obj.get("section"),
            "year": class_obj.get("year"),
            "class_id": class_obj["class_id"],
        }

        return jsonify(
            {
                "class_id": class_obj["class_id"],
                "class_name": f"{class_obj['course']} {class_obj['section']}",
                "class_info": class_info,
                "members": members,
                "total_members": len(members),
            }
        )
    except Exception as e:
        logger.error(f"Failed to get members for class {class_id}: {str(e)}")
        return jsonify({"error": "Failed to get class members"}), 500


@instructor_bp.route(
    "/api/instructor/classes/<int:class_id>/details",
    methods=["GET"],
    endpoint="get_class_details",
)
@login_required
def get_class_details(class_id):
    if session.get("role") != "instructor":
        return jsonify({"error": "Access denied"}), 403

    try:
        with get_db_connection().cursor() as cursor:
            cursor.execute(
                "SELECT id FROM instructors WHERE user_id = %s", (session["user_id"],)
            )
            instructor = cursor.fetchone()
            if not instructor:
                return jsonify({"error": "Instructor profile not found"}), 404

            cursor.execute(
                "SELECT * FROM classes WHERE id = %s AND instructor_id = %s",
                (class_id, instructor["id"]),
            )
            class_obj = cursor.fetchone()
            if not class_obj:
                return jsonify({"error": "Class not found or access denied"}), 404

            cursor.execute(
                """SELECT i.*, pi.first_name, pi.last_name, pi.middle_name, pi.email
                FROM instructors i
                LEFT JOIN personal_info pi ON i.personal_info_id = pi.id
                WHERE i.id = %s""",
                (instructor["id"],),
            )
            instructor_info = cursor.fetchone()

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
                "subject": (
                    class_obj.get("subject")
                    if isinstance(class_obj, dict)
                    else class_obj["subject"]
                ),
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
            {"class_info": class_info, "instructor_info": instructor_details}
        )
    except Exception as e:
        logger.error(f"Failed to get details for class {class_id}: {str(e)}")
        return jsonify({"error": "Failed to get class details"}), 500


@instructor_bp.route("/gradebuilder", endpoint="gradebuilder_entry")
@login_required
def gradebuilder_entry():
    if session.get("role") != "instructor":
        return render_template("unauthorized.html", message="Access denied.")
    return redirect(url_for("instructor.gradebuilder_v2"))


@instructor_bp.route("/gradebuilder-v2", endpoint="gradebuilder_v2")
@login_required
def gradebuilder_v2():
    if session.get("role") != "instructor":
        return render_template("unauthorized.html", message="Access denied.")
    # Render the Grade Builder v2 page for instructors
    return render_template("gradebuilder_v2.html")


@instructor_bp.route("/release-grades", endpoint="release_grades")
@login_required
def release_grades():
    if session.get("role") != "instructor":
        return render_template("unauthorized.html", message="Access denied.")

    try:
        with get_db_connection().cursor() as cursor:
            cursor.execute(
                "SELECT id FROM instructors WHERE user_id = %s", (session["user_id"],)
            )
            instructor = cursor.fetchone()
            if not instructor:
                flash("Instructor profile not found.", "error")
                return redirect(url_for("dashboard.instructor_dashboard"))

            cursor.execute(
                "SELECT * FROM classes WHERE instructor_id = %s ORDER BY created_at DESC",
                (instructor["id"],),
            )
            classes = cursor.fetchall()

            instructor_classes = []
            for cls in classes:
                cursor.execute(
                    "SELECT COUNT(*) as count FROM student_classes WHERE class_id = %s",
                    (cls["id"],),
                )
                member_count = cursor.fetchone()["count"]

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

                instructor_classes.append(
                    {
                        "id": cls["id"],
                        "class_id": computed_class_id,
                        "course": cls["course"],
                        "subject": cls.get("subject"),
                        "track": cls["track"],
                        "section": cls["section"],
                        "schedule": cls["schedule"],
                        "year": cls["year"],
                        "semester": cls["semester"],
                        "class_code": cls["class_code"],
                        "join_code": cls["join_code"],
                        "member_count": member_count,
                    }
                )

            # Ensure the template has access to the current user (some templates expect `user`)
            cursor.execute("SELECT * FROM users WHERE id = %s", (session["user_id"],))
            user = cursor.fetchone()
            if not user:
                session.clear()
                flash("Session expired. Please log in again.", "error")
                return redirect(url_for("auth.login"))

            return render_template(
                "release_grades.html",
                instructor_classes=instructor_classes,
                user=user,
            )
    except Exception as e:
        logger.error(f"Failed to load release grades page: {str(e)}")
        flash("Failed to load page. Please try again.", "error")
        return redirect(url_for("dashboard.instructor_dashboard"))


def _normalize_snapshot(snapshot):
    """Normalize raw snapshot JSON into a UI-friendly structure.

    Returns dict with keys: assessments (list), students (list of {student_id, scores, final_grade, equivalent}).
    """
    try:
        import json as _json
    except Exception:
        _json = None

    if not snapshot:
        return {"assessments": [], "students": []}

    # if snapshot is a string, try to parse
    if isinstance(snapshot, str) and _json:
        try:
            snapshot = _json.loads(snapshot)
        except Exception:
            snapshot = {}

    assessments = snapshot.get("assessments") or []
    students = []
    for s in snapshot.get("students") or []:
        sid = s.get("student_id") or s.get("id")
        try:
            sid_i = int(sid)
        except Exception:
            sid_i = sid
        computed = s.get("computed") or {}
        final_grade = (
            computed.get("final_grade")
            or computed.get("total")
            or computed.get("score")
        )
        try:
            final_grade = None if final_grade is None else round(float(final_grade), 2)
        except Exception:
            final_grade = None
        letter = (
            computed.get("letter_grade")
            or computed.get("equivalent")
            or computed.get("grade_letter")
        )
        # normalize scores
        scores = []
        raw_scores = s.get("scores") or s.get("inputs") or []
        if isinstance(raw_scores, dict):
            for aid, val in raw_scores.items():
                try:
                    aid_i = int(aid)
                except Exception:
                    aid_i = aid
                try:
                    score_val = None if val is None else float(val)
                except Exception:
                    score_val = None
                scores.append({"assessment_id": aid_i, "score": score_val})
        elif isinstance(raw_scores, list):
            for it in raw_scores:
                if isinstance(it, dict):
                    aid = it.get("assessment_id") or it.get("id")
                    try:
                        aid_i = int(aid)
                    except Exception:
                        aid_i = aid
                    val = it.get("score")
                    try:
                        score_val = None if val is None else float(val)
                    except Exception:
                        score_val = None
                    scores.append({"assessment_id": aid_i, "score": score_val})
                else:
                    # fallback: scalar values
                    scores.append({"assessment_id": None, "score": it})

        students.append(
            {
                "student_id": sid_i,
                "scores": scores,
                "final_grade": final_grade,
                "equivalent": letter,
                "computed": computed,
            }
        )

    return {"assessments": assessments, "students": students}


@instructor_bp.route(
    "/instructor/class/<int:class_id>/release-grades",
    methods=["GET"],
    endpoint="api_get_release_grades",
)
@login_required
def api_get_release_grades(class_id):
    """Get grades data for release management sourced from grade snapshots."""

    if session.get("role") != "instructor":
        return jsonify({"error": "forbidden"}), 403

    if not _instructor_owns_class(class_id, session.get("user_id")):
        return jsonify({"error": "unauthorized_class"}), 403

    try:
        with get_db_connection().cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    version,
                    status,
                    snapshot_json,
                    created_at,
                    released_at
                FROM grade_snapshots
                WHERE class_id = %s
                ORDER BY
                    CASE WHEN status = 'final' THEN 0 ELSE 1 END,
                    version DESC,
                    COALESCE(released_at, created_at) DESC
                LIMIT 1
                """,
                (class_id,),
            )

            snapshot_row = cursor.fetchone()
            snapshot_students = {}
            snapshot_meta = {}

            if snapshot_row:
                if isinstance(snapshot_row, dict):
                    snapshot_meta = {
                        "id": snapshot_row.get("id"),
                        "version": snapshot_row.get("version"),
                        "status": snapshot_row.get("status"),
                        "created_at": snapshot_row.get("created_at"),
                        "released_at": snapshot_row.get("released_at"),
                    }
                    snapshot_payload = snapshot_row.get("snapshot_json")
                else:
                    snapshot_meta = {
                        "id": snapshot_row[0],
                        "version": snapshot_row[1],
                        "status": snapshot_row[2],
                        "created_at": snapshot_row[4],
                        "released_at": snapshot_row[5],
                    }
                    snapshot_payload = snapshot_row[3]

                try:
                    normalized = _normalize_snapshot(
                        json.loads(snapshot_payload or "{}")
                    )
                except Exception as exc:
                    logger.error(
                        f"Failed to parse snapshot_json for class {class_id}: {exc}"
                    )
                    return jsonify({"error": "invalid_snapshot_json"}), 500

                for entry in normalized.get("students", []):
                    sid = entry.get("student_id") or entry.get("id")
                    if sid is None:
                        continue
                    try:
                        sid_int = int(sid)
                    except Exception:
                        sid_int = sid
                    snapshot_students[sid_int] = entry

            cursor.execute(
                """
                SELECT
                    sc.student_id,
                    u.school_id,
                    pi.first_name,
                    pi.last_name,
                    pi.middle_name,
                    rg.status,
                    rg.released_at
                FROM student_classes sc
                JOIN students s ON sc.student_id = s.id
                JOIN users u ON s.user_id = u.id
                LEFT JOIN personal_info pi ON s.personal_info_id = pi.id
                LEFT JOIN released_grades rg
                    ON s.id = rg.student_id AND rg.class_id = %s
                WHERE sc.class_id = %s
                ORDER BY pi.last_name, pi.first_name
                """,
                (class_id, class_id),
            )

            rows = cursor.fetchall() or []
            students = []

            def _col(row, key, index):
                if isinstance(row, dict):
                    return row.get(key)
                return row[index]

            snapshot_released_at = (
                snapshot_meta.get("released_at") if snapshot_meta else None
            )

            for row in rows:
                student_id = _col(row, "student_id", 0)
                school_id = (_col(row, "school_id", 1) or "").strip()
                first_name = (_col(row, "first_name", 2) or "").strip()
                last_name = (_col(row, "last_name", 3) or "").strip()
                middle_name = (_col(row, "middle_name", 4) or "").strip()
                status_value = (_col(row, "status", 5) or "").lower()
                is_released = status_value == "released"
                released_value = _col(row, "released_at", 6)

                if first_name and last_name:
                    student_name = (
                        f"{last_name}, {first_name} {middle_name}".strip()
                        if middle_name
                        else f"{last_name}, {first_name}"
                    )
                else:
                    student_name = school_id or f"Student {student_id}"

                snapshot_entry = snapshot_students.get(student_id)
                final_grade = None
                equivalent = "N/A"
                overall_percentage = None

                if snapshot_entry:
                    final_grade = snapshot_entry.get("final_grade")
                    try:
                        final_grade = (
                            None
                            if final_grade is None
                            else round(float(final_grade), 2)
                        )
                    except Exception:
                        final_grade = None

                    equivalent = (
                        snapshot_entry.get("equivalent")
                        or (snapshot_entry.get("computed") or {}).get("letter_grade")
                        or "N/A"
                    )
                    overall_percentage = (snapshot_entry.get("computed") or {}).get(
                        "overall_percentage"
                    )

                if is_released and isinstance(released_value, datetime):
                    released_date = released_value.strftime("%Y-%m-%d")
                elif is_released and isinstance(released_value, str) and released_value:
                    released_date = released_value
                else:
                    released_date = None

                if not released_date and is_released and snapshot_released_at:
                    if isinstance(snapshot_released_at, datetime):
                        released_date = snapshot_released_at.strftime("%Y-%m-%d")
                    else:
                        released_date = str(snapshot_released_at)

                students.append(
                    {
                        "id": student_id,
                        "name": student_name,
                        "school_id": school_id,
                        "final_grade": final_grade,
                        "equivalent": equivalent,
                        "overall_percentage": overall_percentage,
                        "is_released": is_released,
                        "released_date": released_date,
                    }
                )

            response = {
                "class_id": class_id,
                "students": students,
                "total_students": len(students),
            }

            if snapshot_meta:
                response["snapshot"] = {
                    "id": snapshot_meta.get("id"),
                    "version": snapshot_meta.get("version"),
                    "status": snapshot_meta.get("status"),
                    "released_at": (
                        snapshot_meta["released_at"].strftime("%Y-%m-%d %H:%M:%S")
                        if isinstance(snapshot_meta.get("released_at"), datetime)
                        else snapshot_meta.get("released_at")
                    ),
                    "captured_at": (
                        snapshot_meta["created_at"].strftime("%Y-%m-%d %H:%M:%S")
                        if isinstance(snapshot_meta.get("created_at"), datetime)
                        else snapshot_meta.get("created_at")
                    ),
                }

            return jsonify(response)

    except Exception as e:
        logger.error(f"Failed to get release grades for class {class_id}: {str(e)}")
        return jsonify({"error": "failed_to_get_grades"}), 500


def _coerce_student_ids(student_ids):
    normalised = []
    for sid in student_ids or []:
        if sid is None:
            continue
        try:
            normalised.append(int(sid))
        except (TypeError, ValueError):
            continue
    # Deduplicate while preserving deterministic order for SQL bindings
    return sorted(set(normalised))


def _compose_student_display_name(first_name, last_name, middle_name, fallback):
    first = (first_name or "").strip()
    last = (last_name or "").strip()
    middle = (middle_name or "").strip()
    if first and last:
        return f"{last}, {first} {middle}".strip() if middle else f"{last}, {first}"
    return fallback


def _finalize_snapshot_and_store_release(cursor, class_id, student_ids, released_by):
    ids = _coerce_student_ids(student_ids)
    if not ids:
        return {"success": False, "error": "no_valid_student_ids"}

    # Prefer the latest draft snapshot; fall back to most recent final snapshot
    cursor.execute(
        """
        SELECT id, version, status, snapshot_json, created_at, released_at
        FROM grade_snapshots
        WHERE class_id = %s
        ORDER BY CASE WHEN status = 'draft' THEN 0 ELSE 1 END,
                 version DESC,
                 COALESCE(released_at, created_at) DESC
        LIMIT 1
        """,
        (class_id,),
    )
    snapshot_row = cursor.fetchone()
    if not snapshot_row:
        return {"success": False, "error": "snapshot_not_found"}

    snapshot_id = (
        snapshot_row.get("id") if isinstance(snapshot_row, dict) else snapshot_row[0]
    )
    snapshot_status = (
        snapshot_row.get("status")
        if isinstance(snapshot_row, dict)
        else snapshot_row[2]
    )
    snapshot_payload = (
        snapshot_row.get("snapshot_json")
        if isinstance(snapshot_row, dict)
        else snapshot_row[3]
    )
    released_at_value = (
        snapshot_row.get("released_at")
        if isinstance(snapshot_row, dict)
        else snapshot_row[5]
    )

    now = datetime.now()
    if snapshot_status != "final":
        cursor.execute(
            "UPDATE grade_snapshots SET status = 'final', released_at = %s WHERE id = %s",
            (now, snapshot_id),
        )
        released_at_value = now
    elif not released_at_value:
        cursor.execute(
            "UPDATE grade_snapshots SET released_at = %s WHERE id = %s",
            (now, snapshot_id),
        )
        released_at_value = now

    try:
        normalized_snapshot = _normalize_snapshot(snapshot_payload)
    except Exception as exc:
        logger.error(
            f"Failed to normalize snapshot for class {class_id} (snapshot {snapshot_id}): {exc}"
        )
        return {"success": False, "error": "invalid_snapshot_json"}

    student_entries = {}
    for entry in normalized_snapshot.get("students", []):
        sid = entry.get("student_id") or entry.get("id")
        try:
            sid_int = int(sid)
        except Exception:
            sid_int = sid
        student_entries[sid_int] = entry

    placeholders = ",".join(["%s"] * len(ids))
    cursor.execute(
        f"""
        SELECT s.id AS student_id,
               u.school_id,
               pi.first_name,
               pi.last_name,
               pi.middle_name
        FROM students s
        JOIN users u ON s.user_id = u.id
        LEFT JOIN personal_info pi ON s.personal_info_id = pi.id
        WHERE s.id IN ({placeholders})
        """,
        ids,
    )
    profile_map = {}
    for row in cursor.fetchall() or []:
        sid = row.get("student_id")
        fallback = row.get("school_id") or f"Student {sid}"
        profile_map[sid] = {
            "school_id": row.get("school_id"),
            "name": _compose_student_display_name(
                row.get("first_name"),
                row.get("last_name"),
                row.get("middle_name"),
                fallback,
            ),
        }

    for sid in ids:
        profile = profile_map.get(sid, {})
        entry = student_entries.get(sid) or {"student_id": sid}
        computed = entry.get("computed") or {}
        final_grade = entry.get("final_grade")
        try:
            final_grade = None if final_grade is None else round(float(final_grade), 2)
        except Exception:
            final_grade = None
        overall_percentage = computed.get("overall_percentage")
        try:
            overall_percentage = (
                None
                if overall_percentage is None
                else round(float(overall_percentage), 2)
            )
        except Exception:
            overall_percentage = None
        equivalent = entry.get("equivalent") or computed.get("letter_grade") or "N/A"

        cursor.execute(
            """
            INSERT INTO released_grades (
                class_id,
                snapshot_id,
                student_id,
                student_school_id,
                student_name,
                final_grade,
                equivalent,
                overall_percentage,
                status,
                grade_payload,
                released_by,
                released_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'released', %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                snapshot_id = VALUES(snapshot_id),
                student_school_id = VALUES(student_school_id),
                student_name = VALUES(student_name),
                final_grade = VALUES(final_grade),
                equivalent = VALUES(equivalent),
                overall_percentage = VALUES(overall_percentage),
                status = 'released',
                grade_payload = VALUES(grade_payload),
                released_by = VALUES(released_by),
                released_at = VALUES(released_at),
                updated_at = NOW()
            """,
            (
                class_id,
                snapshot_id,
                sid,
                profile.get("school_id"),
                profile.get("name") or f"Student {sid}",
                final_grade,
                equivalent,
                overall_percentage,
                json.dumps(entry),
                released_by,
                released_at_value or now,
            ),
        )

    return {
        "success": True,
        "snapshot_id": snapshot_id,
        "released_at": released_at_value or now,
    }


def _update_released_grade_status(cursor, class_id, student_ids, status):
    ids = _coerce_student_ids(student_ids)
    if not ids:
        return
    placeholders = ",".join(["%s"] * len(ids))
    cursor.execute(
        f"""
        UPDATE released_grades
        SET status = %s,
            released_at = CASE WHEN %s = 'released' THEN COALESCE(released_at, NOW()) ELSE NULL END,
            updated_at = NOW()
        WHERE class_id = %s AND student_id IN ({placeholders})
        """,
        [status, status, class_id, *ids],
    )


@instructor_bp.route(
    "/instructor/student/<int:student_id>/toggle-release",
    methods=["POST"],
    endpoint="api_toggle_student_release",
)
@login_required
def api_toggle_student_release(student_id):
    """Toggle release status for individual student."""
    if session.get("role") != "instructor":
        return jsonify({"error": "forbidden"}), 403

    try:
        data = request.get_json() or {}
        class_id = data.get("class_id")
        release = data.get("release", False)

        if not class_id:
            return jsonify({"error": "class_id_required"}), 400

        # Verify instructor owns this class
        if not _instructor_owns_class(class_id, session.get("user_id")):
            return jsonify({"error": "unauthorized_class"}), 403

        released_at_value = None
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM student_classes WHERE student_id = %s AND class_id = %s",
                    (student_id, class_id),
                )
                if not cursor.fetchone():
                    return jsonify({"error": "student_not_in_class"}), 404

                if release:
                    release_result = _finalize_snapshot_and_store_release(
                        cursor, class_id, [student_id], session.get("user_id")
                    )
                    if not release_result.get("success"):
                        return (
                            jsonify(
                                {
                                    "error": release_result.get(
                                        "error", "failed_to_release"
                                    )
                                }
                            ),
                            400,
                        )
                    released_at_value = release_result.get("released_at")
                else:
                    _update_released_grade_status(
                        cursor, class_id, [student_id], "hidden"
                    )

            conn.commit()
        except Exception:
            conn.rollback()
            raise

        released_date_value = None
        if release and released_at_value:
            if isinstance(released_at_value, datetime):
                released_date_value = released_at_value.strftime("%Y-%m-%d %H:%M:%S")
            else:
                released_date_value = str(released_at_value)

        return jsonify(
            {
                "success": True,
                "student_id": student_id,
                "class_id": class_id,
                "is_released": release,
                "released_date": released_date_value,
            }
        )

    except Exception as e:
        logger.error(
            f"Failed to toggle release status for student {student_id}: {str(e)}"
        )
        return jsonify({"error": "failed_to_update"}), 500


@instructor_bp.route(
    "/instructor/bulk-toggle-release",
    methods=["POST"],
    endpoint="api_bulk_toggle_release",
)
@login_required
def api_bulk_toggle_release():
    """Bulk toggle release status for multiple students."""
    if session.get("role") != "instructor":
        return jsonify({"error": "forbidden"}), 403

    try:
        data = request.get_json() or {}
        class_id = data.get("class_id")
        student_ids = data.get("student_ids", [])
        release = data.get("release", False)
        options = data.get("options", {})

        if not class_id or not student_ids:
            return jsonify({"error": "class_id_and_student_ids_required"}), 400

        # Verify instructor owns this class
        if not _instructor_owns_class(class_id, session.get("user_id")):
            return jsonify({"error": "unauthorized_class"}), 403

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Verify all students are in the class
                placeholders = ",".join(["%s"] * len(student_ids))
                params = student_ids + [class_id]

                cursor.execute(
                    f"""
                    SELECT student_id FROM student_classes
                    WHERE student_id IN ({placeholders}) AND class_id = %s
                """,
                    params,
                )

                valid_students = {row["student_id"] for row in cursor.fetchall() or []}
                invalid_students = set(student_ids) - valid_students

                if invalid_students:
                    return (
                        jsonify(
                            {
                                "error": "some_students_not_in_class",
                                "invalid_students": list(invalid_students),
                            }
                        ),
                        400,
                    )

                release_result = None
                if release:
                    release_result = _finalize_snapshot_and_store_release(
                        cursor, class_id, student_ids, session.get("user_id")
                    )
                    if not release_result.get("success"):
                        return (
                            jsonify(
                                {
                                    "error": release_result.get(
                                        "error", "failed_to_release"
                                    )
                                }
                            ),
                            400,
                        )
                else:
                    _update_released_grade_status(
                        cursor, class_id, student_ids, "hidden"
                    )

            conn.commit()
        except Exception:
            conn.rollback()
            raise

        released_at_value = None
        if release and release_result:
            released_at_value = release_result.get("released_at")

        return jsonify(
            {
                "success": True,
                "class_id": class_id,
                "updated_count": len(student_ids),
                "is_released": release,
                "released_date": (
                    released_at_value.strftime("%Y-%m-%d %H:%M:%S")
                    if isinstance(released_at_value, datetime)
                    else (str(released_at_value) if released_at_value else None)
                ),
            }
        )

    except Exception as e:
        logger.error(f"Failed to bulk toggle release status: {str(e)}")
        return jsonify({"error": "failed_to_bulk_update"}), 500
    return render_template("gradebuilder_v2.html")


@instructor_bp.route("/scores", methods=["GET", "POST"], endpoint="api_list_scores")
@login_required
def api_list_scores():
    instructor_id, err = _require_instructor()
    if err:
        return err

    # POST: accept JSON payload { scores: [ { student_id, assessment_id, class_id, score }, ... ] }
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        scores = data.get("scores")
        if not isinstance(scores, list) or not scores:
            return jsonify({"error": "scores_required"}), 400

        # Validate class ownership: ensure at least one class_id is present and instructor owns it
        try:
            cls_id = int(scores[0].get("class_id", 0))
        except Exception:
            return jsonify({"error": "invalid_class_id"}), 400

        # Ensure all submitted entries belong to the same class
        for s in scores:
            try:
                if int(s.get("class_id", 0)) != cls_id:
                    return jsonify({"error": "mixed_class_ids_not_allowed"}), 400
            except Exception:
                return jsonify({"error": "invalid_class_id_in_payload"}), 400

        if not _instructor_owns_class(cls_id, session.get("user_id")):
            return jsonify({"error": "forbidden"}), 403

        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                # Validate that all referenced assessments exist and belong to this class
                try:
                    aid_set = set()
                    for s in scores:
                        try:
                            aid_set.add(int(s.get("assessment_id")))
                        except Exception:
                            continue
                    if not aid_set:
                        return jsonify({"error": "no_valid_assessment_ids"}), 400
                    placeholders = ",".join(["%s"] * len(aid_set))
                    params = list(aid_set) + [cls_id]
                    cursor.execute(
                        f"SELECT ga.id FROM grade_assessments ga "
                        f"JOIN grade_subcategories gsc ON ga.subcategory_id = gsc.id "
                        f"JOIN grade_categories gc ON gsc.category_id = gc.id "
                        f"JOIN grade_structures gs ON gc.structure_id = gs.id "
                        f"WHERE ga.id IN ({placeholders}) AND gs.class_id = %s",
                        params,
                    )
                    found = {row["id"] for row in (cursor.fetchall() or [])}
                    missing = sorted(list(aid_set - found))
                    if missing:
                        logger.error(
                            f"Attempt to save scores for missing assessments: {missing}"
                        )
                        return (
                            jsonify(
                                {
                                    "error": "assessments_not_found_or_not_belonging_to_class",
                                    "missing": missing,
                                }
                            ),
                            400,
                        )
                except Exception:
                    # If validation query fails for some reason, log and abort
                    logger.exception("Failed to validate assessment ids")
                    return jsonify({"error": "failed_to_validate_assessments"}), 500

                # Validate that all referenced student IDs belong to this class
                try:
                    sid_set = set()
                    for s in scores:
                        try:
                            sid_set.add(int(s.get("student_id")))
                        except Exception:
                            continue
                    if not sid_set:
                        return jsonify({"error": "no_valid_student_ids"}), 400
                    placeholders_s = ",".join(["%s"] * len(sid_set))
                    params_s = list(sid_set) + [cls_id]
                    cursor.execute(
                        f"SELECT sc.student_id FROM student_classes sc WHERE sc.student_id IN ({placeholders_s}) AND sc.class_id = %s",
                        params_s,
                    )
                    found_students = {
                        row["student_id"] for row in (cursor.fetchall() or [])
                    }
                    missing_students = sorted(list(sid_set - found_students))
                    if missing_students:
                        logger.error(
                            f"Attempt to save scores for students not in class: {missing_students}"
                        )
                        return (
                            jsonify(
                                {
                                    "error": "students_not_enrolled_in_class",
                                    "missing": missing_students,
                                }
                            ),
                            400,
                        )
                except Exception:
                    logger.exception("Failed to validate student ids")
                    return jsonify({"error": "failed_to_validate_students"}), 500

                for s in scores:
                    try:
                        sid = int(s.get("student_id"))
                        aid = int(s.get("assessment_id"))
                        val = s.get("score")
                        # treat null/empty as NULL (delete?) but we'll store 0 if missing numeric
                        if val is None or val == "":
                            score_val = 0
                        else:
                            score_val = float(val)
                    except Exception:
                        continue

                    # Check if a student_scores row exists
                    cursor.execute(
                        "SELECT id FROM student_scores WHERE assessment_id = %s AND student_id = %s",
                        (aid, sid),
                    )
                    existing = cursor.fetchone()
                    if existing:
                        cursor.execute(
                            "UPDATE student_scores SET score = %s WHERE id = %s",
                            (score_val, existing["id"]),
                        )
                    else:
                        cursor.execute(
                            "INSERT INTO student_scores (assessment_id, student_id, score) VALUES (%s, %s, %s)",
                            (aid, sid, score_val),
                        )
            try:
                conn.commit()
            except Exception:
                pass

            # Notify live subscribers that class data changed
            try:
                emit_live_version_update(cls_id)
            except Exception:
                pass

            return jsonify({"success": True, "saved": len(scores)}), 200
        except Exception as e:
            logger.error(f"Failed to save scores: {str(e)}")
            return jsonify({"error": "failed_to_save_scores"}), 500

    # GET: existing behavior (list scores by assessment_id or class_id)
    assessment_id = request.args.get("assessment_id")
    class_id = request.args.get("class_id")
    if not assessment_id and not class_id:
        return jsonify({"error": "assessment_id or class_id is required"}), 400

    try:
        with get_db_connection().cursor() as cursor:
            if assessment_id and class_id:
                cursor.execute(
                    """
                    SELECT ss.id, ss.student_id, ss.assessment_id, ss.score
                    FROM student_scores ss
                    JOIN grade_assessments ga ON ss.assessment_id = ga.id
                    JOIN grade_subcategories gsc ON ga.subcategory_id = gsc.id
                    JOIN grade_categories gc ON gsc.category_id = gc.id
                    JOIN grade_structures gs ON gc.structure_id = gs.id
                    WHERE ss.assessment_id = %s AND gs.class_id = %s
                    """,
                    (assessment_id, class_id),
                )
            elif assessment_id:
                cursor.execute(
                    "SELECT id, student_id, assessment_id, score FROM student_scores WHERE assessment_id = %s",
                    (assessment_id,),
                )
            else:
                cursor.execute(
                    """
                    SELECT ss.id, ss.student_id, ss.assessment_id, ss.score
                    FROM student_scores ss
                    JOIN grade_assessments ga ON ss.assessment_id = ga.id
                    JOIN grade_subcategories gsc ON ga.subcategory_id = gsc.id
                    JOIN grade_categories gc ON gsc.category_id = gc.id
                    JOIN grade_structures gs ON gc.structure_id = gs.id
                    WHERE gs.class_id = %s
                    """,
                    (class_id,),
                )
            rows = cursor.fetchall() or []
        return jsonify({"scores": rows}), 200
    except Exception as e:
        logger.error(f"Failed to fetch scores: {str(e)}")
        return jsonify({"error": "failed_to_fetch_scores"}), 500


@instructor_bp.route(
    "/classes/<int:class_id>/save-snapshot",
    methods=["POST"],
    endpoint="api_save_snapshot",
)
@login_required
def api_save_snapshot(class_id: int):
    """Save posted scores, recompute grades and create a grade snapshot (draft).

    Expected POST JSON: { "scores": [ { "student_id": int, "assessment_id": int, "score": number, "class_id": int }, ... ] }
    Returns: { status: "ok", "version": next_version }
    """
    instructor_id, err = _require_instructor()
    if err:
        return err

    # ensure instructor owns class
    if not _instructor_owns_class(class_id, session.get("user_id")):
        return jsonify({"error": "forbidden"}), 403

    data = request.get_json(silent=True) or {}
    scores = data.get("scores")
    if not isinstance(scores, list) or not scores:
        return jsonify({"error": "scores_required"}), 400

    try:
        conn = get_db_connection()
        # Begin transaction
        try:
            conn.begin()
        except Exception:
            pass

        with conn.cursor() as cursor:
            # Validate assessment ids belong to this class
            aid_set = set()
            for s in scores:
                try:
                    aid_set.add(int(s.get("assessment_id")))
                except Exception:
                    continue
            if not aid_set:
                return jsonify({"error": "no_valid_assessment_ids"}), 400

            placeholders = ",".join(["%s"] * len(aid_set))
            params = list(aid_set) + [class_id]
            cursor.execute(
                f"SELECT ga.id FROM grade_assessments ga "
                f"JOIN grade_subcategories gsc ON ga.subcategory_id = gsc.id "
                f"JOIN grade_categories gc ON gsc.category_id = gc.id "
                f"JOIN grade_structures gs ON gc.structure_id = gs.id "
                f"WHERE ga.id IN ({placeholders}) AND gs.class_id = %s",
                params,
            )
            found = {row["id"] for row in (cursor.fetchall() or [])}
            missing = sorted(list(aid_set - found))
            if missing:
                return (
                    jsonify(
                        {
                            "error": "assessments_not_found_or_not_belonging_to_class",
                            "missing": missing,
                        }
                    ),
                    400,
                )

            # Validate student ids belong to this class
            sid_set = set()
            for s in scores:
                try:
                    sid_set.add(int(s.get("student_id")))
                except Exception:
                    continue
            if not sid_set:
                return jsonify({"error": "no_valid_student_ids"}), 400
            placeholders_s = ",".join(["%s"] * len(sid_set))
            params_s = list(sid_set) + [class_id]
            cursor.execute(
                f"SELECT sc.student_id FROM student_classes sc WHERE sc.student_id IN ({placeholders_s}) AND sc.class_id = %s",
                params_s,
            )
            found_students = {row["student_id"] for row in (cursor.fetchall() or [])}
            missing_students = sorted(list(sid_set - found_students))
            if missing_students:
                return (
                    jsonify(
                        {
                            "error": "students_not_enrolled_in_class",
                            "missing": missing_students,
                        }
                    ),
                    400,
                )

            # Upsert posted scores into student_scores
            for s in scores:
                try:
                    sid = int(s.get("student_id"))
                    aid = int(s.get("assessment_id"))
                    val = s.get("score")
                    score_val = 0 if (val is None or val == "") else float(val)
                except Exception:
                    continue

                # Ensure a single row per (assessment_id, student_id): delete existing then insert.
                # This is robust without requiring a DB unique constraint.
                try:
                    cursor.execute(
                        "DELETE FROM student_scores WHERE assessment_id = %s AND student_id = %s",
                        (aid, sid),
                    )
                except Exception:
                    # ignore delete errors and continue to insert
                    pass
                cursor.execute(
                    "INSERT INTO student_scores (assessment_id, student_id, score) VALUES (%s, %s, %s)",
                    (aid, sid, score_val),
                )

            # commit saved scores so recompute reads latest values
            try:
                conn.commit()
            except Exception:
                pass

            # Recompute groups and per-student totals
            # Fetch assessments and their grouping info for this class
            cursor.execute(
                """
                SELECT ga.id AS id, ga.name AS name, ga.max_score AS max_score,
                       gsc.id AS subcategory_id, gsc.name AS subcategory, IFNULL(gsc.weight,0) AS sub_weight,
                       gc.id AS category_id, gc.name AS category, IFNULL(gc.weight,0) AS category_weight
                FROM grade_assessments ga
                JOIN grade_subcategories gsc ON ga.subcategory_id = gsc.id
                JOIN grade_categories gc ON gsc.category_id = gc.id
                JOIN grade_structures gs ON gc.structure_id = gs.id
                WHERE gs.class_id = %s AND gs.is_active = 1
                """,
                (class_id,),
            )
            assessments = cursor.fetchall() or []

            # Build groups payload
            groups = {}
            aid_to_assess = {}
            for a in assessments:
                aid = a["id"]
                aid_to_assess[aid] = {
                    "id": aid,
                    "name": a["name"],
                    "max_score": float(a.get("max_score") or 0),
                    "category": a.get("category") or "",
                    "subcategory": a.get("subcategory") or "",
                    "subweight": float(a.get("sub_weight") or 0),
                }
                key = f"{aid_to_assess[aid]['category']}::{aid_to_assess[aid]['subcategory']}"
                g = groups.get(key) or {
                    "ids": [],
                    "maxes": [],
                    "maxTotal": 0.0,
                    "subweight": aid_to_assess[aid]["subweight"],
                }
                g["ids"].append(aid)
                g["maxes"].append(float(a.get("max_score") or 0))
                g["maxTotal"] = g.get("maxTotal", 0.0) + float(a.get("max_score") or 0)
                groups[key] = g

            # Fetch all student scores for assessments in this class
            if aid_to_assess:
                placeholders_all = ",".join(["%s"] * len(aid_to_assess))
                params_all = list(aid_to_assess.keys())
                cursor.execute(
                    f"SELECT student_id, assessment_id, score FROM student_scores WHERE assessment_id IN ({placeholders_all})",
                    params_all,
                )
                score_rows = cursor.fetchall() or []
            else:
                score_rows = []

            # group scores by student
            by_student = {}
            for r in score_rows:
                sid = r.get("student_id")
                if sid is None:
                    continue
                by_student.setdefault(sid, {})[int(r.get("assessment_id"))] = float(
                    r.get("score") or 0
                )

            snapshot_students = []
            for sid, score_map in by_student.items():
                # compute per-group totals
                category_totals = {}
                weighted_totals = {}
                overall_pct = 0.0
                for gkey, g in groups.items():
                    parts = gkey.split("::")
                    cat = parts[0] or ""
                    sub = parts[1] or ""
                    ids = g.get("ids", [])
                    maxTotal = float(g.get("maxTotal") or 0)
                    total = 0.0
                    for aid in ids:
                        v = score_map.get(aid)
                        if v is None:
                            continue
                        total += float(v or 0)
                    eq_pct = (
                        (float(total) / maxTotal * 100.0)
                        if maxTotal and maxTotal > 0
                        else 0.0
                    )
                    reqpct = round((eq_pct * float(g.get("subweight") or 0)) / 100.0, 2)
                    # store nested category_totals
                    category_totals.setdefault(cat, {})[sub] = round(total, 2)
                    weighted_totals.setdefault(cat, {})[sub] = round(reqpct, 2)

                # compute category ratings = sum of weighted subcategories
                cat_ratings = {}
                for cat, subs in weighted_totals.items():
                    cat_ratings[cat] = round(sum(subs.values()), 2)

                # Derive RAW as UI: RAW = lab_rating * 0.4 + lecture_rating * 0.6
                lecture_val = float(cat_ratings.get("LECTURE", 0) or 0)
                lab_val = float(cat_ratings.get("LABORATORY", 0) or 0)
                raw = round((lab_val * 0.4 + lecture_val * 0.6), 2)
                total_grade = round((raw * 0.625 + 37.5), 2)

                # compute equivalent using helper from utils.grade_calculation
                from utils.grade_calculation import get_equivalent

                snapshot_students.append(
                    {
                        "student_id": sid,
                        "scores": [
                            {"assessment_id": aid, "score": score_map.get(aid, 0)}
                            for aid in sorted(score_map.keys())
                        ],
                        "computed": {
                            "category_totals": category_totals,
                            "weighted_totals": weighted_totals,
                            "category_ratings": cat_ratings,
                            "overall_percentage": raw,
                            "final_grade": total_grade,
                            "letter_grade": get_equivalent(total_grade),
                            "remarks": None,
                        },
                    }
                )

            # Build final snapshot
            snapshot = {
                "meta": {
                    "class_id": class_id,
                    "structure_version": None,
                    "saved_at": datetime.utcnow().isoformat() + "Z",
                },
                "assessments": list(aid_to_assess.values()),
                "students": snapshot_students,
            }

            # Try to include structure version if available
            import json as _json

            try:
                cursor.execute(
                    "SELECT id, version FROM grade_snapshots WHERE class_id = %s AND status = 'draft' ORDER BY version DESC LIMIT 1",
                    (class_id,),
                )
                existing_draft = cursor.fetchone()
            except Exception:
                existing_draft = None

            try:
                if existing_draft:
                    # Update the existing draft snapshot (preserve version)
                    snap_id = existing_draft.get("id")
                    version = int(existing_draft.get("version") or 1)
                    cursor.execute(
                        "UPDATE grade_snapshots SET snapshot_json = %s, created_by = %s, created_at = NOW() WHERE id = %s",
                        (_json.dumps(snapshot), session.get("user_id"), snap_id),
                    )
                else:
                    # No draft exists: insert new snapshot with incremented version
                    try:
                        cursor.execute(
                            "SELECT COALESCE(MAX(version), 0) + 1 AS nextv FROM grade_snapshots WHERE class_id = %s",
                            (class_id,),
                        )
                        rowv = cursor.fetchone() or {"nextv": 1}
                        version = int(rowv.get("nextv") or 1)
                    except Exception:
                        version = 1

                    cursor.execute(
                        "INSERT INTO grade_snapshots (class_id, version, status, snapshot_json, created_by) VALUES (%s, %s, %s, %s, %s)",
                        (
                            class_id,
                            version,
                            "draft",
                            _json.dumps(snapshot),
                            session.get("user_id"),
                        ),
                    )

                try:
                    conn.commit()
                except Exception:
                    pass
            except Exception as e:
                # rollback and return error
                try:
                    conn.rollback()
                except Exception:
                    pass
                logger.exception("Failed to write snapshot")
                return (
                    jsonify({"error": "failed_to_write_snapshot", "message": str(e)}),
                    500,
                )

        # Notify live update
        try:
            emit_live_version_update(class_id)
        except Exception:
            pass

        return jsonify({"status": "ok", "version": version}), 200
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        logger.exception("Error saving snapshot")
        return jsonify({"error": "failed_to_save_snapshot", "message": str(e)}), 500


@instructor_bp.route(
    "/instructor/class/<int:class_id>/grades",
    methods=["GET"],
    endpoint="instructor_class_grades",
)
@login_required
def instructor_class_grades(class_id: int):
    if session.get("role") != "instructor":
        session.clear()
        flash("Unauthorized access.", "error")
        return redirect(url_for("auth.login"))

    if not _instructor_owns_class(class_id, session.get("user_id")):
        flash("You do not have access to this class.", "error")
        return redirect(url_for("dashboard.instructor_dashboard"))

    try:
        with get_db_connection().cursor() as cursor:
            cursor.execute(
                """
                SELECT gs.*, c.course, c.track, c.section, c.class_type,
                       c.subject, c.year, c.semester, c.schedule, c.class_code, c.join_code
                FROM grade_structures gs
                JOIN classes c ON gs.class_id = c.id
                WHERE gs.class_id = %s AND gs.is_active = 1
                """,
                (class_id,),
            )
            grade_structure = cursor.fetchone()
            if not grade_structure:
                flash("No active grading structure found for this class.", "error")
                return redirect(url_for("dashboard.instructor_dashboard"))

            structure = (
                json.loads(grade_structure["structure_json"])
                if grade_structure.get("structure_json")
                else {}
            )

            # Ensure normalized categories/subcategories exist for this structure so we can map names -> IDs
            try:
                with get_db_connection().cursor() as c2:
                    # Fetch existing categories for this structure
                    c2.execute(
                        "SELECT id, name FROM grade_categories WHERE structure_id = %s ORDER BY position",
                        (grade_structure.get("id"),),
                    )
                    existing_cats = {
                        row["name"]: row["id"] for row in (c2.fetchall() or [])
                    }

                    # Create missing top-level categories (LECTURE/LABORATORY)
                    desired_cats = [
                        k for k in ("LECTURE", "LABORATORY") if structure.get(k)
                    ]
                    pos = 1
                    for cat_name in desired_cats:
                        if cat_name not in existing_cats:
                            c2.execute(
                                """
                                INSERT INTO grade_categories (structure_id, name, weight, position, description, created_at)
                                VALUES (%s, %s, %s, %s, %s, NOW())
                                """,
                                (grade_structure.get("id"), cat_name, 100.0, pos, None),
                            )
                            existing_cats[cat_name] = (
                                getattr(c2, "lastrowid", None) or 0
                            )
                        pos += 1

                    # For each subcategory in the structure JSON, ensure a row exists under its category
                    for cat_name in desired_cats:
                        cat_id = existing_cats.get(cat_name)
                        if not cat_id:
                            continue
                        # load existing subs for this category
                        c2.execute(
                            "SELECT id, name FROM grade_subcategories WHERE category_id = %s ORDER BY position",
                            (cat_id,),
                        )
                        existing_subs = {
                            row["name"]: row["id"] for row in (c2.fetchall() or [])
                        }
                        # insert any missing subs from structure JSON
                        subs = structure.get(cat_name) or []
                        sub_pos = 1
                        for subdef in subs:
                            try:
                                sub_name = (subdef or {}).get("name")
                                sub_weight = float((subdef or {}).get("weight") or 0)
                            except Exception:
                                sub_name, sub_weight = (None, 0.0)
                            if not sub_name:
                                continue
                            if sub_name not in existing_subs:
                                # max_score is required by schema; use 0 as placeholder for subcategory level
                                c2.execute(
                                    """
                                    INSERT INTO grade_subcategories (category_id, name, weight, max_score, position, description, created_at)
                                    VALUES (%s, %s, %s, %s, %s, %s, NOW())
                                    """,
                                    (cat_id, sub_name, sub_weight, 0.0, sub_pos, None),
                                )
                                existing_subs[sub_name] = (
                                    getattr(c2, "lastrowid", None) or 0
                                )
                            sub_pos += 1
                try:
                    conn.commit()
                except Exception:
                    pass
            except Exception:
                # Non-fatal: if ensuring fails, page may still render, but add-assessment will warn
                pass

            cursor.execute(
                """
                SELECT
                    ga.id, ga.name, ga.max_score,
                    gsc.name AS subcategory_name,
                    gc.name AS category_name
                FROM grade_assessments ga
                JOIN grade_subcategories gsc ON ga.subcategory_id = gsc.id
                JOIN grade_categories gc ON gsc.category_id = gc.id
                JOIN grade_structures gs ON gc.structure_id = gs.id
                WHERE gs.class_id = %s AND gs.is_active = 1
                ORDER BY gc.position, gsc.position, ga.position, ga.id
                """,
                (class_id,),
            )
            assessments = cursor.fetchall() or []

            cursor.execute(
                """
                SELECT 
                    sc.student_id,
                    u.school_id,
                    pi.first_name, pi.last_name, pi.middle_name
                FROM student_classes sc
                JOIN students s ON sc.student_id = s.id
                JOIN users u ON s.user_id = u.id
                LEFT JOIN personal_info pi ON s.personal_info_id = pi.id
                WHERE sc.class_id = %s
                ORDER BY pi.last_name, pi.first_name
                """,
                (class_id,),
            )
            enrollments = cursor.fetchall() or []

            students = []
            for e in enrollments:
                first_name = e.get("first_name") or ""
                middle_name = e.get("middle_name") or ""
                last_name = e.get("last_name") or ""
                school_id = e.get("school_id") or ""
                if first_name and last_name:
                    student_name = (
                        f"{last_name}, {first_name} {middle_name}".strip()
                        if middle_name
                        else f"{last_name}, {first_name}"
                    )
                else:
                    student_name = school_id or f"Student {e.get('student_id')}"
                students.append(
                    {
                        "id": e.get("student_id"),
                        "name": student_name,
                        "school_id": school_id,
                    }
                )

            scores_map = {}
            if assessments:
                cursor.execute(
                    """
                    SELECT ss.student_id, ss.assessment_id, ss.score
                    FROM student_scores ss
                    JOIN grade_assessments ga ON ss.assessment_id = ga.id
                    JOIN grade_subcategories gsc ON ga.subcategory_id = gsc.id
                    JOIN grade_categories gc ON gsc.category_id = gc.id
                    JOIN grade_structures gs ON gc.structure_id = gs.id
                    WHERE gs.class_id = %s
                    """,
                    (class_id,),
                )
                for row in cursor.fetchall() or []:
                    scores_map[(row["student_id"], row["assessment_id"])] = row["score"]

            from collections import defaultdict

            by_cat = defaultdict(lambda: defaultdict(list))
            for a in assessments:
                by_cat[a["category_name"]][a["subcategory_name"]].append(a)

            sub_id_map = {}
            try:
                with get_db_connection().cursor() as cursor2:
                    cursor2.execute(
                        """
                        SELECT gsc.id AS sub_id, gsc.name AS sub_name, gc.name AS cat_name
                        FROM grade_subcategories gsc
                        JOIN grade_categories gc ON gsc.category_id = gc.id
                        WHERE gc.structure_id = %s
                        """,
                        (grade_structure.get("id"),),
                    )
                    for r in cursor2.fetchall() or []:
                        catn = r.get("cat_name")
                        subn = r.get("sub_name")
                        sid = r.get("sub_id")
                        if catn and subn and sid:
                            sub_id_map.setdefault(catn, {})[subn] = sid
            except Exception:
                sub_id_map = {}

            # Build class_info for template display
            class_info = {
                "course": grade_structure.get("course"),
                "subject": grade_structure.get("subject"),
                "year": grade_structure.get("year"),
                "semester": grade_structure.get("semester"),
                "track": grade_structure.get("track"),
                "section": grade_structure.get("section"),
                "schedule": grade_structure.get("schedule"),
                "class_code": grade_structure.get("class_code"),
                "join_code": grade_structure.get("join_code"),
                "class_type": grade_structure.get("class_type"),
            }

            return render_template(
                "instructor_grades_unified.html",
                class_id=class_id,
                structure_id=grade_structure.get("id"),
                structure_name=grade_structure.get("structure_name"),
                structure=structure,
                students=students,
                assessments=assessments,
                scores_map=scores_map,
                grouped_assessments=by_cat,
                sub_id_map=sub_id_map,
                csrf_token=generate_csrf(),
                class_info=class_info,
            )
    except Exception as e:
        import traceback

        logger.error(
            f"Error in instructor_class_grades: {str(e)}\n{traceback.format_exc()}"
        )
        return f"<pre style='color:red;'>{traceback.format_exc()}</pre>"


@instructor_bp.route(
    "/api/instructor/class/<int:class_id>/has-structure",
    methods=["GET"],
    endpoint="api_has_active_structure",
)
@login_required
def api_has_active_structure(class_id: int):
    if session.get("role") != "instructor":
        return jsonify({"error": "forbidden"}), 403
    try:
        if not _instructor_owns_class(class_id, session.get("user_id")):
            return jsonify({"error": "unauthorized_class"}), 403
        with get_db_connection().cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM grade_structures WHERE class_id = %s AND is_active = 1 LIMIT 1",
                (class_id,),
            )
            row = cursor.fetchone()
            return jsonify({"class_id": class_id, "has_structure": bool(row)}), 200
    except Exception as e:
        logger.error(f"has-structure check failed for class {class_id}: {str(e)}")
        return jsonify({"error": "failed_to_check"}), 500


@instructor_bp.route("/statistics", endpoint="instructor_statistics")
@login_required
def instructor_statistics():
    if session.get("role") != "instructor":
        flash("Access denied. Instructor privileges required.", "error")
        return redirect(url_for("home"))

    try:
        with get_db_connection().cursor() as cursor:
            # Get user data
            cursor.execute("SELECT * FROM users WHERE id = %s", (session["user_id"],))
            user = cursor.fetchone()

            # Get instructor ID
            cursor.execute(
                "SELECT id FROM instructors WHERE user_id = %s", (session["user_id"],)
            )
            instructor = cursor.fetchone()
            if not instructor:
                flash("Instructor profile not found.", "error")
                return redirect(url_for("dashboard.instructor_dashboard"))

            instructor_id = instructor["id"]

            # Get total classes
            cursor.execute(
                "SELECT COUNT(*) as count FROM classes WHERE instructor_id = %s",
                (instructor_id,),
            )
            total_classes = cursor.fetchone()["count"]

            # Get total unique students across all classes
            cursor.execute(
                """
                SELECT COUNT(DISTINCT sc.student_id) as count 
                FROM student_classes sc 
                JOIN classes c ON sc.class_id = c.id 
                WHERE c.instructor_id = %s
            """,
                (instructor_id,),
            )
            total_students = cursor.fetchone()["count"]

            # Get average class size
            avg_class_size = total_students / total_classes if total_classes > 0 else 0

            # Get semester/year breakdown
            cursor.execute(
                """
                SELECT year, semester, COUNT(*) as class_count
                FROM classes 
                WHERE instructor_id = %s 
                GROUP BY year, semester 
                ORDER BY year DESC, semester DESC
            """,
                (instructor_id,),
            )
            semester_data = cursor.fetchall()

            # Get assessment count per class
            cursor.execute(
                """
                SELECT c.class_code, c.subject, COUNT(DISTINCT ga.id) as assessment_count
                FROM classes c
                LEFT JOIN grade_structures gs ON c.id = gs.class_id AND gs.is_active = 1
                LEFT JOIN grade_categories gc ON gs.id = gc.structure_id
                LEFT JOIN grade_subcategories gsc ON gc.id = gsc.category_id
                LEFT JOIN grade_assessments ga ON gsc.id = ga.subcategory_id
                WHERE c.instructor_id = %s
                GROUP BY c.id, c.class_code, c.subject
                ORDER BY c.created_at DESC
            """,
                (instructor_id,),
            )
            assessment_data = cursor.fetchall()

            # Get classes with student counts and assessment counts
            cursor.execute(
                """
                SELECT c.id, c.class_code, c.subject, c.course, c.section, 
                       COUNT(DISTINCT sc.student_id) as student_count,
                       COUNT(DISTINCT ga.id) as assessment_count
                FROM classes c 
                LEFT JOIN student_classes sc ON c.id = sc.class_id 
                LEFT JOIN grade_structures gs ON c.id = gs.class_id AND gs.is_active = 1
                LEFT JOIN grade_categories gc ON gs.id = gc.structure_id
                LEFT JOIN grade_subcategories gsc ON gc.id = gsc.category_id
                LEFT JOIN grade_assessments ga ON gsc.id = ga.subcategory_id
                WHERE c.instructor_id = %s 
                GROUP BY c.id, c.class_code, c.subject, c.course, c.section
                ORDER BY c.created_at DESC
            """,
                (instructor_id,),
            )
            classes_data = cursor.fetchall()

            # Calculate grade statistics from student_scores and grade_assessments
            grade_stats = {}
            try:
                # Get assessment statistics for this instructor's classes
                cursor.execute(
                    """
                    SELECT 
                        COUNT(ss.id) as total_scores,
                        AVG(ss.score) as avg_score,
                        MIN(ss.score) as min_score,
                        MAX(ss.score) as max_score,
                        COUNT(DISTINCT ss.student_id) as students_with_scores,
                        COUNT(DISTINCT ga.id) as total_assessments
                    FROM student_scores ss
                    JOIN grade_assessments ga ON ss.assessment_id = ga.id
                    JOIN grade_subcategories gsc ON ga.subcategory_id = gsc.id
                    JOIN grade_categories gc ON gsc.category_id = gc.id
                    JOIN grade_structures gs ON gc.structure_id = gs.id
                    WHERE gs.class_id IN (
                        SELECT id FROM classes WHERE instructor_id = %s
                    )
                """,
                    (instructor_id,),
                )
                score_row = cursor.fetchone()

                if score_row and score_row["total_scores"] > 0:
                    grade_stats = {
                        "total_scores": score_row["total_scores"],
                        "avg_score": round(score_row["avg_score"] or 0, 2),
                        "min_score": score_row["min_score"] or 0,
                        "max_score": score_row["max_score"] or 0,
                        "students_with_scores": score_row["students_with_scores"],
                        "total_assessments": score_row["total_assessments"],
                        "score_range": f"{score_row['min_score'] or 0} - {score_row['max_score'] or 0}",
                    }

                    # Calculate pass rate based on a 60% passing threshold
                    cursor.execute(
                        """
                        SELECT 
                            COUNT(*) as total_scores,
                            SUM(CASE WHEN ss.score >= 60 THEN 1 ELSE 0 END) as passing_scores
                        FROM student_scores ss
                        JOIN grade_assessments ga ON ss.assessment_id = ga.id
                        JOIN grade_subcategories gsc ON ga.subcategory_id = gsc.id
                        JOIN grade_categories gc ON gsc.category_id = gc.id
                        JOIN grade_structures gs ON gc.structure_id = gs.id
                        WHERE gs.class_id IN (
                            SELECT id FROM classes WHERE instructor_id = %s
                        )
                    """,
                        (instructor_id,),
                    )
                    pass_row = cursor.fetchone()
                    if pass_row and pass_row["total_scores"] > 0:
                        grade_stats["pass_rate"] = round(
                            (pass_row["passing_scores"] / pass_row["total_scores"])
                            * 100,
                            1,
                        )
                        grade_stats["passing_count"] = pass_row["passing_scores"]
                        grade_stats["failing_count"] = (
                            pass_row["total_scores"] - pass_row["passing_scores"]
                        )
            except Exception as e:
                logger.warning(f"Could not calculate grade statistics: {str(e)}")
                grade_stats = {}

            stats = {
                "total_classes": total_classes,
                "total_students": total_students,
                "avg_class_size": round(avg_class_size, 1),
                "classes": classes_data,
                "grade_stats": grade_stats,
                "semester_data": semester_data,
                "assessment_data": assessment_data,
            }

    except Exception as e:
        logger.error(f"Error loading instructor statistics: {str(e)}")
        flash("Error loading statistics.", "error")
        return redirect(url_for("dashboard.instructor_dashboard"))

    return render_template("instructor_statistics.html", stats=stats, user=user)


@instructor_bp.route("/data-simulation", endpoint="data_simulation")
@login_required
def data_simulation():
    if session.get("role") != "instructor":
        flash("Access denied. Instructor privileges required.", "error")
        return redirect(url_for("home"))

    try:
        with get_db_connection().cursor() as cursor:
            # Get user data
            cursor.execute("SELECT * FROM users WHERE id = %s", (session["user_id"],))
            user = cursor.fetchone()

            # Get instructor ID
            cursor.execute(
                "SELECT id FROM instructors WHERE user_id = %s", (session["user_id"],)
            )
            instructor = cursor.fetchone()
            if not instructor:
                flash("Instructor profile not found.", "error")
                return redirect(url_for("dashboard.instructor_dashboard"))

            instructor_id = instructor["id"]

            # Get available classes for simulation
            cursor.execute(
                """
                SELECT c.id, c.class_code, c.subject, c.course, c.section,
                       COUNT(DISTINCT stc.student_id) as student_count,
                       COUNT(DISTINCT ss.id) as score_count
                FROM classes c
                LEFT JOIN student_classes stc ON c.id = stc.class_id
                LEFT JOIN students s ON stc.student_id = s.id
                LEFT JOIN student_scores ss ON s.id = ss.student_id
                WHERE c.instructor_id = %s
                GROUP BY c.id, c.class_code, c.subject, c.course, c.section
                ORDER BY c.created_at DESC
            """,
                (instructor_id,),
            )
            available_classes = cursor.fetchall()

            # Debug logging
            logger.info(
                f"Instructor {session.get('school_id')} accessing data simulation. Found {len(available_classes)} classes."
            )

            # Get assessment types available
            cursor.execute(
                """
                SELECT DISTINCT ga.id, ga.name, ga.max_score
                FROM grade_assessments ga
                WHERE ga.id IN (
                    SELECT DISTINCT ss.assessment_id
                    FROM student_scores ss
                    JOIN students s ON ss.student_id = s.id
                    JOIN student_classes sc ON s.id = sc.student_id
                    JOIN classes c ON sc.class_id = c.id
                    WHERE c.instructor_id = %s
                )
                ORDER BY ga.name
            """,
                (instructor_id,),
            )
            available_assessments = cursor.fetchall()

    except Exception as e:
        logger.error(f"Error loading data simulation page: {str(e)}")
        flash("Error loading data simulation.", "error")
        return redirect(url_for("dashboard.instructor_dashboard"))

    return render_template(
        "data_simulation.html",
        user=user,
        available_classes=available_classes or [],
        available_assessments=available_assessments or [],
    )


@instructor_bp.route(
    "/api/data-simulation/analyze",
    methods=["POST"],
    endpoint="api_data_simulation_analyze",
)
@login_required
def api_data_simulation_analyze():
    if session.get("role") != "instructor":
        return jsonify({"error": "forbidden"}), 403

    try:
        data = request.get_json(silent=True) or {}
        analysis_type = data.get("analysis_type")
        class_ids = data.get("class_ids", [])
        assessment_ids = data.get("assessment_ids", [])
        prediction_target = data.get("prediction_target")

        if not analysis_type or not class_ids:
            return jsonify({"error": "Missing required parameters"}), 400

        with get_db_connection().cursor() as cursor:
            # Get instructor ID
            cursor.execute(
                "SELECT id FROM instructors WHERE user_id = %s", (session["user_id"],)
            )
            instructor = cursor.fetchone()
            if not instructor:
                return jsonify({"error": "Instructor not found"}), 404

            instructor_id = instructor["id"]

            # Verify classes belong to instructor
            cursor.execute(
                """
                SELECT id FROM classes WHERE instructor_id = %s AND id IN %s
            """,
                (
                    instructor_id,
                    tuple(class_ids) if len(class_ids) > 1 else (class_ids[0],),
                ),
            )
            valid_classes = cursor.fetchall()
            if len(valid_classes) != len(class_ids):
                return jsonify({"error": "Invalid class selection"}), 400

            results = {}

            if analysis_type == "pass_fail":
                results = perform_pass_fail_analysis(cursor, class_ids, assessment_ids)
            elif analysis_type == "maintaining":
                results = perform_maintaining_analysis(
                    cursor, class_ids, assessment_ids
                )
            elif analysis_type == "failing":
                results = perform_failing_analysis(cursor, class_ids, assessment_ids)
            elif analysis_type == "top_performers":
                results = perform_top_performers_analysis(
                    cursor, class_ids, assessment_ids
                )
            elif analysis_type == "grade_trends":
                results = perform_grade_trends_analysis(
                    cursor, class_ids, assessment_ids
                )
            elif analysis_type == "assessment_difficulty":
                results = perform_assessment_difficulty_analysis(
                    cursor, class_ids, assessment_ids
                )
            elif analysis_type == "consistency":
                results = perform_consistency_analysis(
                    cursor, class_ids, assessment_ids
                )
            elif analysis_type == "peer_comparison":
                results = perform_peer_comparison_analysis(
                    cursor, class_ids, assessment_ids
                )
            elif analysis_type == "risk_prediction":
                results = perform_risk_prediction_analysis(
                    cursor, class_ids, assessment_ids
                )
            else:
                return jsonify({"error": "Invalid analysis type"}), 400

            return jsonify(results)

    except Exception as e:
        logger.error(f"Data simulation analysis error: {str(e)}")
        return jsonify({"error": "Analysis failed", "details": str(e)}), 500


def perform_pass_fail_analysis(cursor, class_ids, assessment_ids):
    """Analyze pass/fail rates and grade distribution"""
    try:
        query = """
            SELECT
                s.id as student_id,
                CONCAT(pi.first_name, ' ', pi.last_name) as student_name,
                ga.name as assessment_name,
                ss.score,
                ga.max_score
            FROM student_scores ss
            JOIN grade_assessments ga ON ss.assessment_id = ga.id
            JOIN students s ON ss.student_id = s.id
            LEFT JOIN personal_info pi ON s.personal_info_id = pi.id
            JOIN student_classes sc ON s.id = sc.student_id
            WHERE sc.class_id IN %s
        """
        params = (tuple(class_ids) if len(class_ids) > 1 else (class_ids[0],),)

        if assessment_ids:
            query += " AND ga.id IN %s"
            params += (
                (
                    tuple(assessment_ids)
                    if len(assessment_ids) > 1
                    else (assessment_ids[0],)
                ),
            )

        cursor.execute(query, params)
        scores_data = cursor.fetchall()

        # Calculate student averages
        from collections import defaultdict
        import numpy as np

        student_scores = defaultdict(list)

        for row in scores_data:
            student_id = row["student_id"]
            score_percentage = (
                (row["score"] / row["max_score"]) * 100 if row["max_score"] > 0 else 0
            )
            student_scores[student_id].append(score_percentage)

        # Calculate averages and pass/fail
        student_averages = {}
        pass_count = 0
        fail_count = 0
        grade_distribution = {
            "90-100% (A)": {"count": 0, "percentage": 0},
            "80-89% (B)": {"count": 0, "percentage": 0},
            "70-79% (C)": {"count": 0, "percentage": 0},
            "60-69% (D)": {"count": 0, "percentage": 0},
            "Below 60% (F)": {"count": 0, "percentage": 0},
        }

        for student_id, scores in student_scores.items():
            avg_score = np.mean(scores)
            student_averages[student_id] = avg_score

            if avg_score >= 60:  # Assuming 60% is passing
                pass_count += 1
            else:
                fail_count += 1

            # Grade distribution
            if avg_score >= 90:
                grade_distribution["90-100% (A)"]["count"] += 1
            elif avg_score >= 80:
                grade_distribution["80-89% (B)"]["count"] += 1
            elif avg_score >= 70:
                grade_distribution["70-79% (C)"]["count"] += 1
            elif avg_score >= 60:
                grade_distribution["60-69% (D)"]["count"] += 1
            else:
                grade_distribution["Below 60% (F)"]["count"] += 1

        total_students = len(student_averages)

        # Calculate percentages
        for grade_range in grade_distribution.values():
            grade_range["percentage"] = (
                round((grade_range["count"] / total_students) * 100, 1)
                if total_students > 0
                else 0
            )

        return {
            "analysis_type": "pass_fail",
            "total_students": total_students,
            "total_assessments": len(
                set(row["assessment_name"] for row in scores_data)
            ),
            "pass_count": pass_count,
            "fail_count": fail_count,
            "pass_percentage": (
                round((pass_count / total_students) * 100, 1)
                if total_students > 0
                else 0
            ),
            "fail_percentage": (
                round((fail_count / total_students) * 100, 1)
                if total_students > 0
                else 0
            ),
            "grade_distribution": grade_distribution,
        }

    except Exception as e:
        return {"error": f"Pass/Fail analysis failed: {str(e)}"}


def perform_maintaining_analysis(cursor, class_ids, assessment_ids):
    """Identify students who are maintaining good academic performance"""
    try:
        query = """
            SELECT
                s.id as student_id,
                CONCAT(pi.first_name, ' ', pi.last_name) as student_name,
                ga.name as assessment_name,
                ss.score,
                ga.max_score
            FROM student_scores ss
            JOIN grade_assessments ga ON ss.assessment_id = ga.id
            JOIN students s ON ss.student_id = s.id
            LEFT JOIN personal_info pi ON s.personal_info_id = pi.id
            JOIN student_classes sc ON s.id = sc.student_id
            WHERE sc.class_id IN %s
        """
        params = (tuple(class_ids) if len(class_ids) > 1 else (class_ids[0],),)

        if assessment_ids:
            query += " AND ga.id IN %s"
            params += (
                (
                    tuple(assessment_ids)
                    if len(assessment_ids) > 1
                    else (assessment_ids[0],)
                ),
            )

        cursor.execute(query, params)
        scores_data = cursor.fetchall()

        # Calculate student averages
        from collections import defaultdict
        import numpy as np

        student_data = defaultdict(lambda: {"scores": [], "assessments": set()})

        for row in scores_data:
            student_id = row["student_id"]
            student_name = row["student_name"]
            score_percentage = (
                (row["score"] / row["max_score"]) * 100 if row["max_score"] > 0 else 0
            )
            student_data[student_id]["name"] = student_name
            student_data[student_id]["scores"].append(score_percentage)
            student_data[student_id]["assessments"].add(row["assessment_name"])

        # Calculate maintaining students (above 75% average)
        maintaining_threshold = 75
        maintaining_students = []
        maintaining_count = 0

        for student_id, data in student_data.items():
            if data["scores"]:
                avg_score = np.mean(data["scores"])
                if avg_score >= maintaining_threshold:
                    maintaining_students.append(
                        {
                            "id": student_id,
                            "name": data["name"],
                            "average_score": round(avg_score, 1),
                            "assessment_count": len(data["assessments"]),
                        }
                    )
                    maintaining_count += 1

        # Sort by average score descending
        maintaining_students.sort(key=lambda x: x["average_score"], reverse=True)

        total_students = len(student_data)

        return {
            "analysis_type": "maintaining",
            "maintaining_threshold": maintaining_threshold,
            "maintaining_count": maintaining_count,
            "maintaining_percentage": (
                round((maintaining_count / total_students) * 100, 1)
                if total_students > 0
                else 0
            ),
            "maintaining_students": maintaining_students,
            "total_students": total_students,
        }

    except Exception as e:
        return {"error": f"Maintaining analysis failed: {str(e)}"}


def perform_failing_analysis(cursor, class_ids, assessment_ids):
    """Identify students who are consistently failing"""
    try:
        query = """
            SELECT
                s.id as student_id,
                CONCAT(pi.first_name, ' ', pi.last_name) as student_name,
                ga.name as assessment_name,
                ss.score,
                ga.max_score
            FROM student_scores ss
            JOIN grade_assessments ga ON ss.assessment_id = ga.id
            JOIN students s ON ss.student_id = s.id
            LEFT JOIN personal_info pi ON s.personal_info_id = pi.id
            JOIN student_classes sc ON s.id = sc.student_id
            WHERE sc.class_id IN %s
        """
        params = (tuple(class_ids) if len(class_ids) > 1 else (class_ids[0],),)

        if assessment_ids:
            query += " AND ga.id IN %s"
            params += (
                (
                    tuple(assessment_ids)
                    if len(assessment_ids) > 1
                    else (assessment_ids[0],)
                ),
            )

        cursor.execute(query, params)
        scores_data = cursor.fetchall()

        # Calculate student averages
        from collections import defaultdict
        import numpy as np

        student_data = defaultdict(lambda: {"scores": [], "assessments": set()})

        for row in scores_data:
            student_id = row["student_id"]
            student_name = row["student_name"]
            score_percentage = (
                (row["score"] / row["max_score"]) * 100 if row["max_score"] > 0 else 0
            )
            student_data[student_id]["name"] = student_name
            student_data[student_id]["scores"].append(score_percentage)
            student_data[student_id]["assessments"].add(row["assessment_name"])

        # Calculate failing students (below 60% average)
        failing_threshold = 60
        failing_students = []
        failing_count = 0

        for student_id, data in student_data.items():
            if data["scores"]:
                avg_score = np.mean(data["scores"])
                if avg_score < failing_threshold:
                    failing_students.append(
                        {
                            "id": student_id,
                            "name": data["name"],
                            "average_score": round(avg_score, 1),
                            "assessment_count": len(data["assessments"]),
                        }
                    )
                    failing_count += 1

        # Sort by average score ascending (worst first)
        failing_students.sort(key=lambda x: x["average_score"])

        total_students = len(student_data)

        return {
            "analysis_type": "failing",
            "failing_threshold": failing_threshold,
            "failing_count": failing_count,
            "failing_percentage": (
                round((failing_count / total_students) * 100, 1)
                if total_students > 0
                else 0
            ),
            "failing_students": failing_students,
            "total_students": total_students,
        }

    except Exception as e:
        return {"error": f"Failing analysis failed: {str(e)}"}


def perform_top_performers_analysis(cursor, class_ids, assessment_ids):
    """Identify top 10 performing students"""
    try:
        query = """
            SELECT
                s.id as student_id,
                CONCAT(pi.first_name, ' ', pi.last_name) as student_name,
                ga.name as assessment_name,
                ss.score,
                ga.max_score
            FROM student_scores ss
            JOIN grade_assessments ga ON ss.assessment_id = ga.id
            JOIN students s ON ss.student_id = s.id
            LEFT JOIN personal_info pi ON s.personal_info_id = pi.id
            JOIN student_classes sc ON s.id = sc.student_id
            WHERE sc.class_id IN %s
        """
        params = (tuple(class_ids) if len(class_ids) > 1 else (class_ids[0],),)

        if assessment_ids:
            query += " AND ga.id IN %s"
            params += (
                (
                    tuple(assessment_ids)
                    if len(assessment_ids) > 1
                    else (assessment_ids[0],)
                ),
            )

        cursor.execute(query, params)
        scores_data = cursor.fetchall()

        # Calculate student averages
        from collections import defaultdict
        import numpy as np

        student_data = defaultdict(lambda: {"scores": [], "assessments": set()})

        for row in scores_data:
            student_id = row["student_id"]
            student_name = row["student_name"]
            score_percentage = (
                (row["score"] / row["max_score"]) * 100 if row["max_score"] > 0 else 0
            )
            student_data[student_id]["name"] = student_name
            student_data[student_id]["scores"].append(score_percentage)
            student_data[student_id]["assessments"].add(row["assessment_name"])

        # Calculate all student averages
        all_students = []
        for student_id, data in student_data.items():
            if data["scores"]:
                avg_score = np.mean(data["scores"])
                all_students.append(
                    {
                        "id": student_id,
                        "name": data["name"],
                        "average_score": round(avg_score, 1),
                        "assessment_count": len(data["assessments"]),
                    }
                )

        # Sort by average score descending and get top 10
        all_students.sort(key=lambda x: x["average_score"], reverse=True)
        top_students = all_students[:10]

        # Calculate class average
        if all_students:
            class_average = np.mean([s["average_score"] for s in all_students])
        else:
            class_average = 0

        return {
            "analysis_type": "top_performers",
            "top_students": top_students,
            "class_average": round(class_average, 1),
            "total_students": len(all_students),
        }

    except Exception as e:
        return {"error": f"Top performers analysis failed: {str(e)}"}


def perform_grade_trends_analysis(cursor, class_ids, assessment_ids):
    """Analyze grade trends over time for students"""
    try:
        query = """
            SELECT
                s.id as student_id,
                CONCAT(pi.first_name, ' ', pi.last_name) as student_name,
                ga.name as assessment_name,
                ss.score,
                ga.max_score,
                ga.created_at
            FROM student_scores ss
            JOIN grade_assessments ga ON ss.assessment_id = ga.id
            JOIN students s ON ss.student_id = s.id
            LEFT JOIN personal_info pi ON s.personal_info_id = pi.id
            JOIN student_classes sc ON s.id = sc.student_id
            WHERE sc.class_id IN %s
        """
        params = (tuple(class_ids) if len(class_ids) > 1 else (class_ids[0],),)

        if assessment_ids:
            query += " AND ga.id IN %s"
            params += (
                (
                    tuple(assessment_ids)
                    if len(assessment_ids) > 1
                    else (assessment_ids[0],)
                ),
            )

        query += " ORDER BY s.id, ga.created_at"

        cursor.execute(query, params)
        scores_data = cursor.fetchall()

        # Group scores by student and calculate trends
        from collections import defaultdict
        import numpy as np

        student_scores = defaultdict(list)

        for row in scores_data:
            student_id = row["student_id"]
            score_percentage = (
                (row["score"] / row["max_score"]) * 100 if row["max_score"] > 0 else 0
            )
            student_scores[student_id].append(
                {
                    "name": row["student_name"],
                    "score": score_percentage,
                    "assessment": row["assessment_name"],
                }
            )

        # Calculate trends
        improving_count = 0
        declining_count = 0
        stable_count = 0
        significant_changes = []

        for student_id, scores in student_scores.items():
            if len(scores) >= 3:  # Need at least 3 assessments for trend analysis
                score_values = [s["score"] for s in scores]
                first_half = np.mean(score_values[: len(score_values) // 2])
                second_half = np.mean(score_values[len(score_values) // 2 :])

                change = second_half - first_half

                if abs(change) >= 10:  # Significant change threshold
                    trend = "improving" if change > 0 else "declining"
                    significant_changes.append(
                        {
                            "id": student_id,
                            "name": scores[0]["name"],
                            "trend": trend,
                            "change": round(change, 1),
                            "assessment_count": len(scores),
                        }
                    )

                    if change > 0:
                        improving_count += 1
                    else:
                        declining_count += 1
                else:
                    stable_count += 1

        total_students = len(student_scores)

        return {
            "analysis_type": "grade_trends",
            "improving_count": improving_count,
            "improving_percentage": (
                round((improving_count / total_students) * 100, 1)
                if total_students > 0
                else 0
            ),
            "declining_count": declining_count,
            "declining_percentage": (
                round((declining_count / total_students) * 100, 1)
                if total_students > 0
                else 0
            ),
            "stable_count": stable_count,
            "stable_percentage": (
                round((stable_count / total_students) * 100, 1)
                if total_students > 0
                else 0
            ),
            "significant_changes": significant_changes,
            "total_students": total_students,
        }

    except Exception as e:
        return {"error": f"Grade trends analysis failed: {str(e)}"}


def perform_assessment_difficulty_analysis(cursor, class_ids, assessment_ids):
    """Analyze which assessments are most/least difficult"""
    try:
        query = """
            SELECT
                ga.name as assessment_name,
                ss.score,
                ga.max_score
            FROM student_scores ss
            JOIN grade_assessments ga ON ss.assessment_id = ga.id
            JOIN students s ON ss.student_id = s.id
            JOIN student_classes sc ON s.id = sc.student_id
            WHERE sc.class_id IN %s
        """
        params = (tuple(class_ids) if len(class_ids) > 1 else (class_ids[0],),)

        if assessment_ids:
            query += " AND ga.id IN %s"
            params += (
                (
                    tuple(assessment_ids)
                    if len(assessment_ids) > 1
                    else (assessment_ids[0],)
                ),
            )

        cursor.execute(query, params)
        scores_data = cursor.fetchall()

        # Calculate assessment averages
        from collections import defaultdict
        import numpy as np

        assessment_scores = defaultdict(list)

        for row in scores_data:
            assessment_name = row["assessment_name"]
            score_percentage = (
                (row["score"] / row["max_score"]) * 100 if row["max_score"] > 0 else 0
            )
            assessment_scores[assessment_name].append(score_percentage)

        # Calculate class average
        all_scores = []
        for scores in assessment_scores.values():
            all_scores.extend(scores)
        class_average = np.mean(all_scores) if all_scores else 0

        # Rank assessments by difficulty
        assessments = []
        for assessment_name, scores in assessment_scores.items():
            avg_score = np.mean(scores)
            difficulty = (
                "Very Easy"
                if avg_score >= 85
                else (
                    "Easy"
                    if avg_score >= 75
                    else (
                        "Moderate"
                        if avg_score >= 65
                        else "Hard" if avg_score >= 55 else "Very Hard"
                    )
                )
            )

            assessments.append(
                {
                    "name": assessment_name,
                    "average_score": round(avg_score, 1),
                    "difficulty": difficulty,
                    "student_count": len(scores),
                }
            )

        # Sort by average score descending (easiest first)
        assessments.sort(key=lambda x: x["average_score"], reverse=True)

        return {
            "analysis_type": "assessment_difficulty",
            "assessments": assessments,
            "class_average": round(class_average, 1),
            "total_assessments": len(assessments),
        }

    except Exception as e:
        return {"error": f"Assessment difficulty analysis failed: {str(e)}"}


def perform_consistency_analysis(cursor, class_ids, assessment_ids):
    """Analyze student consistency in performance"""
    try:
        query = """
            SELECT
                s.id as student_id,
                CONCAT(pi.first_name, ' ', pi.last_name) as student_name,
                ga.name as assessment_name,
                ss.score,
                ga.max_score
            FROM student_scores ss
            JOIN grade_assessments ga ON ss.assessment_id = ga.id
            JOIN students s ON ss.student_id = s.id
            LEFT JOIN personal_info pi ON s.personal_info_id = pi.id
            JOIN student_classes sc ON s.id = sc.student_id
            WHERE sc.class_id IN %s
        """
        params = (tuple(class_ids) if len(class_ids) > 1 else (class_ids[0],),)

        if assessment_ids:
            query += " AND ga.id IN %s"
            params += (
                (
                    tuple(assessment_ids)
                    if len(assessment_ids) > 1
                    else (assessment_ids[0],)
                ),
            )

        cursor.execute(query, params)
        scores_data = cursor.fetchall()

        # Calculate student consistency
        from collections import defaultdict
        import numpy as np

        student_scores = defaultdict(list)

        for row in scores_data:
            student_id = row["student_id"]
            score_percentage = (
                (row["score"] / row["max_score"]) * 100 if row["max_score"] > 0 else 0
            )
            student_scores[student_id].append(
                {"name": row["student_name"], "score": score_percentage}
            )

        # Calculate consistency metrics
        consistency_rankings = []
        highly_consistent_count = 0
        variable_count = 0

        for student_id, scores in student_scores.items():
            if len(scores) >= 3:  # Need multiple assessments
                score_values = [s["score"] for s in scores]
                mean_score = np.mean(score_values)
                std_dev = np.std(score_values)
                grade_range = max(score_values) - min(score_values)

                # Consistency score (lower std_dev = more consistent)
                consistency_score = std_dev

                consistency_level = (
                    "Very Consistent"
                    if std_dev <= 5
                    else (
                        "Consistent"
                        if std_dev <= 10
                        else (
                            "Moderate"
                            if std_dev <= 15
                            else "Variable" if std_dev <= 20 else "Very Variable"
                        )
                    )
                )

                consistency_rankings.append(
                    {
                        "id": student_id,
                        "name": scores[0]["name"],
                        "consistency_score": round(consistency_score, 1),
                        "consistency_level": consistency_level,
                        "grade_range": round(grade_range, 1),
                        "average_score": round(mean_score, 1),
                        "assessment_count": len(scores),
                    }
                )

                if consistency_level in ["Very Consistent", "Consistent"]:
                    highly_consistent_count += 1
                elif consistency_level in ["Variable", "Very Variable"]:
                    variable_count += 1

        # Sort by consistency score ascending (most consistent first)
        consistency_rankings.sort(key=lambda x: x["consistency_score"])

        total_students = len([s for s in student_scores.values() if len(s) >= 3])

        return {
            "analysis_type": "consistency",
            "consistency_rankings": consistency_rankings,
            "highly_consistent_count": highly_consistent_count,
            "highly_consistent_percentage": (
                round((highly_consistent_count / total_students) * 100, 1)
                if total_students > 0
                else 0
            ),
            "variable_count": variable_count,
            "variable_percentage": (
                round((variable_count / total_students) * 100, 1)
                if total_students > 0
                else 0
            ),
            "total_students": total_students,
        }

    except Exception as e:
        return {"error": f"Consistency analysis failed: {str(e)}"}


def perform_peer_comparison_analysis(cursor, class_ids, assessment_ids):
    """Compare each student to their peers"""
    try:
        query = """
            SELECT
                s.id as student_id,
                CONCAT(pi.first_name, ' ', pi.last_name) as student_name,
                ga.name as assessment_name,
                ss.score,
                ga.max_score
            FROM student_scores ss
            JOIN grade_assessments ga ON ss.assessment_id = ga.id
            JOIN students s ON ss.student_id = s.id
            LEFT JOIN personal_info pi ON s.personal_info_id = pi.id
            JOIN student_classes sc ON s.id = sc.student_id
            WHERE sc.class_id IN %s
        """
        params = (tuple(class_ids) if len(class_ids) > 1 else (class_ids[0],),)

        if assessment_ids:
            query += " AND ga.id IN %s"
            params += (
                (
                    tuple(assessment_ids)
                    if len(assessment_ids) > 1
                    else (assessment_ids[0],)
                ),
            )

        cursor.execute(query, params)
        scores_data = cursor.fetchall()

        # Calculate student averages
        from collections import defaultdict
        import numpy as np

        student_scores = defaultdict(list)

        for row in scores_data:
            student_id = row["student_id"]
            score_percentage = (
                (row["score"] / row["max_score"]) * 100 if row["max_score"] > 0 else 0
            )
            student_scores[student_id].append(
                {"name": row["student_name"], "score": score_percentage}
            )

        # Calculate averages and peer comparison
        student_averages = []
        for student_id, scores in student_scores.items():
            avg_score = np.mean([s["score"] for s in scores])
            student_averages.append(
                {
                    "id": student_id,
                    "name": scores[0]["name"],
                    "average_score": round(avg_score, 1),
                    "assessment_count": len(scores),
                }
            )

        # Calculate class average
        class_avg = (
            np.mean([s["average_score"] for s in student_averages])
            if student_averages
            else 0
        )

        # Calculate peer rankings and percentiles
        peer_rankings = []
        above_average_count = 0
        at_average_count = 0
        below_average_count = 0

        for student in student_averages:
            vs_average = student["average_score"] - class_avg
            percentile = (
                sum(
                    1
                    for s in student_averages
                    if s["average_score"] <= student["average_score"]
                )
                / len(student_averages)
            ) * 100

            peer_rankings.append(
                {
                    "id": student["id"],
                    "name": student["name"],
                    "average_score": student["average_score"],
                    "vs_average": round(vs_average, 1),
                    "percentile": round(percentile, 1),
                    "assessment_count": student["assessment_count"],
                }
            )

            if vs_average > 10:
                above_average_count += 1
            elif vs_average < -10:
                below_average_count += 1
            else:
                at_average_count += 1

        # Sort by average score descending
        peer_rankings.sort(key=lambda x: x["average_score"], reverse=True)

        total_students = len(student_averages)

        return {
            "analysis_type": "peer_comparison",
            "peer_rankings": peer_rankings,
            "class_average": round(class_avg, 1),
            "above_average_count": above_average_count,
            "above_average_percentage": (
                round((above_average_count / total_students) * 100, 1)
                if total_students > 0
                else 0
            ),
            "at_average_count": at_average_count,
            "at_average_percentage": (
                round((at_average_count / total_students) * 100, 1)
                if total_students > 0
                else 0
            ),
            "below_average_count": below_average_count,
            "below_average_percentage": (
                round((below_average_count / total_students) * 100, 1)
                if total_students > 0
                else 0
            ),
            "total_students": total_students,
        }

    except Exception as e:
        return {"error": f"Peer comparison analysis failed: {str(e)}"}


def perform_risk_prediction_analysis(cursor, class_ids, assessment_ids):
    """Predict students at risk of failing"""
    try:
        query = """
            SELECT
                s.id as student_id,
                CONCAT(pi.first_name, ' ', pi.last_name) as student_name,
                ga.name as assessment_name,
                ss.score,
                ga.max_score
            FROM student_scores ss
            JOIN grade_assessments ga ON ss.assessment_id = ga.id
            JOIN students s ON ss.student_id = s.id
            LEFT JOIN personal_info pi ON s.personal_info_id = pi.id
            JOIN student_classes sc ON s.id = sc.student_id
            WHERE sc.class_id IN %s
        """
        params = (tuple(class_ids) if len(class_ids) > 1 else (class_ids[0],),)

        if assessment_ids:
            query += " AND ga.id IN %s"
            params += (
                (
                    tuple(assessment_ids)
                    if len(assessment_ids) > 1
                    else (assessment_ids[0],)
                ),
            )

        cursor.execute(query, params)
        scores_data = cursor.fetchall()

        # Calculate current student performance
        from collections import defaultdict
        import numpy as np

        student_scores = defaultdict(list)

        for row in scores_data:
            student_id = row["student_id"]
            score_percentage = (
                (row["score"] / row["max_score"]) * 100 if row["max_score"] > 0 else 0
            )
            student_scores[student_id].append(
                {"name": row["student_name"], "score": score_percentage}
            )

        # Predict risk based on current performance and trends
        at_risk_students = []
        high_risk_count = 0
        medium_risk_count = 0
        low_risk_count = 0

        for student_id, scores in student_scores.items():
            if len(scores) >= 2:
                score_values = [s["score"] for s in scores]
                current_average = np.mean(score_values)

                # Simple risk prediction based on current average and consistency
                std_dev = np.std(score_values)
                trend_factor = 0

                if len(scores) >= 3:
                    # Calculate trend (recent vs earlier performance)
                    mid_point = len(scores) // 2
                    early_avg = np.mean(score_values[:mid_point])
                    recent_avg = np.mean(score_values[mid_point:])
                    trend_factor = recent_avg - early_avg

                # Risk assessment
                risk_score = 0

                # Low current average increases risk
                if current_average < 60:
                    risk_score += 3
                elif current_average < 70:
                    risk_score += 2
                elif current_average < 80:
                    risk_score += 1

                # High variability increases risk
                if std_dev > 15:
                    risk_score += 1

                # Declining trend increases risk
                if trend_factor < -5:
                    risk_score += 1

                # Determine risk level and predicted final grade
                if risk_score >= 3:
                    risk_level = "High"
                    predicted_final = max(50, current_average - 10)
                    high_risk_count += 1
                elif risk_score >= 2:
                    risk_level = "Medium"
                    predicted_final = max(55, current_average - 5)
                    medium_risk_count += 1
                else:
                    risk_level = "Low"
                    predicted_final = min(95, current_average + 5)
                    low_risk_count += 1

                if risk_level in ["High", "Medium"]:
                    at_risk_students.append(
                        {
                            "id": student_id,
                            "name": scores[0]["name"],
                            "risk_level": risk_level,
                            "current_average": round(current_average, 1),
                            "predicted_final": round(predicted_final, 1),
                            "assessment_count": len(scores),
                        }
                    )

        # Sort by risk level (High first) then by current average
        at_risk_students.sort(
            key=lambda x: (0 if x["risk_level"] == "High" else 1, x["current_average"])
        )

        return {
            "analysis_type": "risk_prediction",
            "at_risk_students": at_risk_students,
            "high_risk_count": high_risk_count,
            "medium_risk_count": medium_risk_count,
            "low_risk_count": low_risk_count,
            "total_students": len(student_scores),
        }

    except Exception as e:
        return {"error": f"Risk prediction analysis failed: {str(e)}"}


@instructor_bp.route("/api/classes/<int:class_id>/calculate", methods=["GET"])
@login_required
def api_calculate_class_grades(class_id):
    """Calculate grades for all students in a class using shared computation logic."""
    # Allow both instructors and students to access, but filter appropriately
    user_role = session.get("role")
    if user_role not in ["instructor", "student"]:
        return jsonify({"error": "Access denied"}), 403

    try:
        with get_db_connection().cursor() as cursor:
            # Verify class exists and user has access
            if user_role == "instructor":
                instructor_id, err = _require_instructor()
                if err:
                    return err
                if not _instructor_owns_class(class_id, session.get("user_id")):
                    return jsonify({"error": "Access denied to this class"}), 403
            elif user_role == "student":
                # Students can only calculate for classes they're enrolled in
                cursor.execute(
                    "SELECT id FROM students WHERE user_id = %s", (session["user_id"],)
                )
                student = cursor.fetchone()
                if not student:
                    return jsonify({"error": "Student profile not found"}), 404
                cursor.execute(
                    "SELECT 1 FROM student_classes WHERE student_id = %s AND class_id = %s",
                    (student["id"], class_id),
                )
                if not cursor.fetchone():
                    return jsonify({"error": "Not enrolled in this class"}), 403

            # Get active grade structure
            cursor.execute(
                "SELECT structure_json FROM grade_structures WHERE class_id = %s AND is_active = 1",
                (class_id,),
            )
            structure_row = cursor.fetchone()
            if not structure_row:
                return (
                    jsonify(
                        {"error": "No active grade structure found for this class"}
                    ),
                    404,
                )

            structure_json = json.loads(structure_row["structure_json"])

            # Get all assessments for this class
            cursor.execute(
                """
                SELECT ga.id, ga.name, ga.max_score, gsc.category_id, gsc.name as subcategory_name,
                       gc.name as category_name
                FROM grade_assessments ga
                JOIN grade_subcategories gsc ON ga.subcategory_id = gsc.id
                JOIN grade_categories gc ON gsc.category_id = gc.id
                JOIN grade_structures gs ON gc.structure_id = gs.id
                WHERE gs.class_id = %s AND gs.is_active = 1
                """,
                (class_id,),
            )
            assessments = cursor.fetchall()

            # Build normalized_rows for computation
            normalized_rows = []
            for assessment in assessments:
                normalized_rows.append(
                    {
                        "assessment": assessment["name"],
                        "category": assessment["category_name"],
                        "name": assessment["subcategory_name"],
                        "weight": 0,  # Will be set from structure
                        "max_score": assessment["max_score"],
                    }
                )

            # Set weights from structure
            for category_name, subcats in structure_json.items():
                for subcat in subcats:
                    for row in normalized_rows:
                        if (
                            row["category"] == category_name
                            and row["name"] == subcat["name"]
                        ):
                            row["weight"] = subcat.get("weight", 0)

            # Get all student scores
            cursor.execute(
                """
                SELECT ss.student_id, ss.score, ga.name as assessment_name
                FROM student_scores ss
                JOIN grade_assessments ga ON ss.assessment_id = ga.id
                WHERE ga.id IN (
                    SELECT ga2.id FROM grade_assessments ga2
                    JOIN grade_subcategories gsc ON ga2.subcategory_id = gsc.id
                    JOIN grade_categories gc ON gsc.category_id = gc.id
                    JOIN grade_structures gs ON gc.structure_id = gs.id
                    WHERE gs.class_id = %s AND gs.is_active = 1
                )
                """,
                (class_id,),
            )
            scores = cursor.fetchall()

            # Build student_scores_named
            student_scores_named = []
            for score in scores:
                student_scores_named.append(
                    {
                        "student_id": score["student_id"],
                        "assessment_name": score["assessment_name"],
                        "score": score["score"],
                    }
                )

            # Perform computation
            from utils.grade_calculation import perform_grade_computation

            computed_grades = perform_grade_computation(
                structure_json, normalized_rows, student_scores_named
            )

            return jsonify({"class_id": class_id, "computed_grades": computed_grades})

    except Exception as e:
        logger.error(f"Failed to calculate class grades: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to calculate grades"}), 500


@instructor_bp.route("/api/instructor/class/<int:class_id>/calculate", methods=["GET"])
@login_required
def api_instructor_calculate_class_grades(class_id):
    """Instructor-specific calculate endpoint - same as general but instructor-only access."""
    instructor_id, err = _require_instructor()
    if err:
        return err

    if not _instructor_owns_class(class_id, session.get("user_id")):
        return jsonify({"error": "Access denied to this class"}), 403

    # Reuse the general calculate logic
    return api_calculate_class_grades(class_id)


@instructor_bp.route("/api/instructor/grades-overview", methods=["GET"])
@login_required
def api_instructor_grades_overview():
    """Get computed grades overview for all classes and students of the instructor."""
    instructor_id, err = _require_instructor()
    if err:
        return err

    try:
        with get_db_connection().cursor() as cursor:
            # Get all classes for this instructor
            cursor.execute(
                "SELECT id, class_code, course, subject, section FROM classes WHERE instructor_id = %s",
                (instructor_id,),
            )
            classes = cursor.fetchall()

            overview_data = []

            for class_info in classes:
                class_id = class_info["id"]

                # Check if class has active structure
                cursor.execute(
                    "SELECT id FROM grade_structures WHERE class_id = %s AND is_active = 1",
                    (class_id,),
                )
                structure = cursor.fetchone()
                if not structure:
                    continue

                # Get computed grades for this class
                try:
                    # Reuse the calculate logic
                    response = api_calculate_class_grades(class_id)
                    if hasattr(response, "get_json"):
                        computed_data = response.get_json()
                    else:
                        # If it's a Response object, get the data differently
                        continue

                    if "computed_grades" in computed_data:
                        class_overview = {
                            "class_id": class_id,
                            "class_code": class_info["class_code"],
                            "course": class_info["course"],
                            "subject": class_info["subject"],
                            "section": class_info["section"],
                            "computed_grades": computed_data["computed_grades"],
                        }
                        overview_data.append(class_overview)

                except Exception as e:
                    logger.warning(
                        f"Failed to compute grades for class {class_id}: {str(e)}"
                    )
                    continue

            return jsonify(
                {"overview": overview_data, "total_classes": len(overview_data)}
            )

    except Exception as e:
        logger.error(
            f"Failed to load instructor grades overview: {str(e)}", exc_info=True
        )
        return jsonify({"error": "Failed to load grades overview"}), 500
