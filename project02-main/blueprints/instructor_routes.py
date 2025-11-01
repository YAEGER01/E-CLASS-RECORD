import logging
import json
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
        with get_db_connection().cursor() as cursor:
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
                rpos.get("pos") if isinstance(rpos, dict) else (rpos[0] if rpos else 1)
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
        try:
            get_db_connection().commit()
        except Exception:
            pass
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

    try:
        with get_db_connection().cursor() as cursor:
            cursor.execute(
                "SELECT id FROM instructors WHERE user_id = %s", (session["user_id"],)
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
            cursor.execute("SELECT id FROM classes WHERE join_code = %s", (join_code,))
            while cursor.fetchone():
                class_code, join_code = _generate_class_codes()
                cursor.execute(
                    "SELECT id FROM classes WHERE join_code = %s", (join_code,)
                )

            cursor.execute(
                """INSERT INTO classes
                (instructor_id, class_type, year, semester, course, track, section, schedule, class_code, join_code)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    instructor["id"],
                    data["classType"],
                    data["year"],
                    data["semester"],
                    data["course"],
                    data["track"],
                    section,
                    data["schedule"],
                    class_code,
                    join_code,
                ),
            )

            class_id = cursor.lastrowid
            get_db_connection().commit()

            logger.info(
                f"Instructor {session.get('school_id')} created class: {data['year']}-{data['semester']} {data['course']} {section}"
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
                        "track": data["track"],
                        "section": section,
                        "schedule": data["schedule"],
                        "class_id": f"{data['year'][-2:]}-{('1' if '1st' in data['semester'].lower() else '2')} {data['course']} {section}",
                        "class_code": class_code,
                        "join_code": join_code,
                    },
                }
            )
    except Exception as e:
        get_db_connection().rollback()
        logger.error(
            f"Failed to create class for instructor {session.get('school_id')}: {str(e)}"
        )
        return jsonify({"error": "Failed to create class"}), 500


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
        return jsonify(
            {
                "class_id": class_obj["class_id"],
                "class_name": f"{class_obj['course']} {class_obj['section']}",
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
    return render_template("gradebuilder_v2.html")


@instructor_bp.route("/api/scores", methods=["GET"], endpoint="api_list_scores")
@login_required
def api_list_scores():
    instructor_id, err = _require_instructor()
    if err:
        return err

    assessment_id = request.args.get("assessment_id")
    class_id = request.args.get("class_id")
    if not assessment_id and not class_id:
        return jsonify({"error": "assessment_id or class_id is required"}), 400

    try:
        with get_db_connection().cursor() as cursor:
            if assessment_id and class_id:
                cursor.execute(
                    """
                    SELECT s.id, s.student_id, s.assessment_id, s.score
                    FROM scores s
                    JOIN assessments a ON s.assessment_id = a.id
                    WHERE s.assessment_id = %s AND a.class_id = %s
                    """,
                    (assessment_id, class_id),
                )
            elif assessment_id:
                cursor.execute(
                    "SELECT id, student_id, assessment_id, score FROM scores WHERE assessment_id = %s",
                    (assessment_id,),
                )
            else:
                cursor.execute(
                    """
                    SELECT s.id, s.student_id, s.assessment_id, s.score
                    FROM scores s
                    JOIN assessments a ON s.assessment_id = a.id
                    WHERE a.class_id = %s
                    """,
                    (class_id,),
                )
            rows = cursor.fetchall() or []
        return jsonify({"scores": rows}), 200
    except Exception as e:
        logger.error(f"Failed to fetch scores: {str(e)}")
        return jsonify({"error": "failed_to_fetch_scores"}), 500


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
                SELECT gs.*, c.course, c.track, c.section, c.class_type
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
                    get_db_connection().commit()
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
