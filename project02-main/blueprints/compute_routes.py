import json
import logging
from datetime import datetime
from flask import Blueprint, jsonify, session

from utils.db_conn import get_db_connection
from utils.live import (
    get_cached_class_live_version,
    _cache_get,
    _cache_put,
    _grouped_cache_get,
    _grouped_cache_put,
)
from utils.auth_utils import login_required
from utils.structure_utils import normalize_structure, group_structure
from utils.grade_calculation import perform_grade_computation

logger = logging.getLogger(__name__)


compute_bp = Blueprint("compute", __name__)


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


@compute_bp.route(
    "/api/classes/<int:class_id>/normalized",
    methods=["GET"],
    endpoint="api_get_normalized",
)
@login_required
def api_get_normalized(class_id: int):
    role = session.get("role")
    if role == "instructor":
        if not _instructor_owns_class(class_id, session.get("user_id")):
            return jsonify({"error": "access_denied"}), 403
    elif role == "admin":
        pass
    else:
        return jsonify({"error": "access_denied"}), 403

    try:
        live_version = get_cached_class_live_version(class_id) or "noversion"
        cache_key = f"{class_id}:{live_version}"

        cached = _cache_get(cache_key)
        if cached is not None:
            return (
                jsonify({"class_id": class_id, "normalized": cached, "cached": True}),
                200,
            )

        with get_db_connection().cursor() as cursor:
            cursor.execute(
                """
                SELECT structure_json
                FROM grade_structures
                WHERE class_id = %s AND is_active = 1
                ORDER BY updated_at DESC
                LIMIT 1
                """,
                (class_id,),
            )
            row = cursor.fetchone()

        if not row:
            return jsonify({"error": "no_active_structure"}), 404

        structure = (
            json.loads(row["structure_json"]) if row.get("structure_json") else {}
        )
        normalized = normalize_structure(structure)
        _cache_put(cache_key, normalized)
        return (
            jsonify({"class_id": class_id, "normalized": normalized, "cached": False}),
            200,
        )
    except Exception as e:
        logger.error(f"Failed to normalize class {class_id}: {str(e)}")
        return jsonify({"error": "failed_to_normalize"}), 500


@compute_bp.route(
    "/api/classes/<int:class_id>/grouped", methods=["GET"], endpoint="api_get_grouped"
)
@login_required
def api_get_grouped(class_id: int):
    role = session.get("role")
    if role == "instructor":
        if not _instructor_owns_class(class_id, session.get("user_id")):
            return jsonify({"error": "access_denied"}), 403
    elif role == "admin":
        pass
    else:
        return jsonify({"error": "access_denied"}), 403

    try:
        live_version = get_cached_class_live_version(class_id) or "noversion"
        cache_key = f"{class_id}:{live_version}"

        cached = _grouped_cache_get(cache_key)
        if cached is not None:
            return (
                jsonify({"class_id": class_id, "grouped": cached, "cached": True}),
                200,
            )

        with get_db_connection().cursor() as cursor:
            cursor.execute(
                """
                SELECT structure_json
                FROM grade_structures
                WHERE class_id = %s AND is_active = 1
                ORDER BY updated_at DESC
                LIMIT 1
                """,
                (class_id,),
            )
            row = cursor.fetchone()

        if not row:
            return jsonify({"error": "no_active_structure"}), 404

        structure = (
            json.loads(row["structure_json"]) if row.get("structure_json") else {}
        )
        normalized = normalize_structure(structure)
        grouped = group_structure(normalized)
        _grouped_cache_put(cache_key, grouped)
        return jsonify({"class_id": class_id, "grouped": grouped, "cached": False}), 200
    except Exception as e:
        logger.error(f"Failed to group class {class_id}: {str(e)}")
        return jsonify({"error": "failed_to_group"}), 500


@compute_bp.route(
    "/api/classes/<int:class_id>/calculate",
    methods=["GET"],
    endpoint="api_calculate_grades",
)
@login_required
def api_calculate_grades(class_id: int):
    role = session.get("role")
    if role == "instructor":
        if not _instructor_owns_class(class_id, session.get("user_id")):
            return jsonify({"error": "access_denied"}), 403
    elif role == "admin":
        pass
    else:
        return jsonify({"error": "access_denied"}), 403

    try:
        # Load structure
        with get_db_connection().cursor() as cursor:
            cursor.execute(
                """
                SELECT structure_json, id
                FROM grade_structures
                WHERE class_id = %s AND is_active = 1
                ORDER BY updated_at DESC
                LIMIT 1
                """,
                (class_id,),
            )
            row = cursor.fetchone()
        if not row:
            return jsonify({"error": "no_active_structure"}), 404

        structure = (
            json.loads(row["structure_json"]) if row.get("structure_json") else {}
        )
        normalized = normalize_structure(structure)

        # Resolve formula (placeholder: empty dict implies use structure weights only)
        formula = {}

        # Load student scores with names
        with get_db_connection().cursor() as cursor:
            cursor.execute(
                """
                SELECT ss.student_id, ga.name AS assessment_name, ss.score
                FROM student_scores ss
                JOIN grade_assessments ga ON ss.assessment_id = ga.id
                JOIN grade_subcategories gsc ON ga.subcategory_id = gsc.id
                JOIN grade_categories gc ON gsc.category_id = gc.id
                JOIN grade_structures gs ON gc.structure_id = gs.id
                WHERE gs.class_id = %s AND gs.is_active = 1
                """,
                (class_id,),
            )
            student_scores = cursor.fetchall() or []

        results = perform_grade_computation(formula, normalized, student_scores)
        return (
            jsonify(
                {
                    "class_id": class_id,
                    "results": results,
                    "used_formula": bool(formula),
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Failed to calculate grades for class {class_id}: {str(e)}")
        return jsonify({"error": "failed_to_calculate"}), 500


@compute_bp.route(
    "/api/classes/<int:class_id>/live-version",
    methods=["GET"],
    endpoint="get_class_live_version",
)
@login_required
def get_class_live_version(class_id: int):
    try:
        version = get_cached_class_live_version(class_id)
        if not version:
            return jsonify({"error": "Failed to compute version"}), 500
        return jsonify({"version": version, "generated_at": datetime.now().isoformat()})
    except Exception as e:
        logger.error(f"Failed to compute live version for class {class_id}: {str(e)}")
        return jsonify({"error": "Failed to compute version"}), 500


@compute_bp.route(
    "/api/compute/class/<int:class_id>",
    methods=["POST"],
    endpoint="compute_class_grades",
)
def compute_class_grades(class_id):
    """Compute final grades for all students in a class using normalized model.

    Returns JSON with per-student computed values:
    {
      "student_id": {"final_percentage": .., "transmuted": .., "equivalent": ".."},
      ...
    }
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM grade_structures WHERE class_id = %s AND is_active = 1 ORDER BY version DESC LIMIT 1",
                (class_id,),
            )
            row = cur.fetchone()
            if not row:
                return jsonify({"error": "No active grade structure for class"}), 404

            structure_id = row["id"] if isinstance(row, dict) else row[0]

            cur.execute(
                "SELECT id, name, weight FROM grade_categories WHERE structure_id = %s ORDER BY position",
                (structure_id,),
            )
            categories = cur.fetchall()

            cat_map = []
            for cat in categories:
                cat_id = cat["id"] if isinstance(cat, dict) else cat[0]
                cur.execute(
                    "SELECT id, name, weight, max_score FROM grade_subcategories WHERE category_id = %s ORDER BY position",
                    (cat_id,),
                )
                subs = cur.fetchall()
                sub_list = []
                for s in subs:
                    sid = s["id"] if isinstance(s, dict) else s[0]
                    sub_list.append(
                        {
                            "id": sid,
                            "name": s["name"] if isinstance(s, dict) else s[1],
                            "weight": float(
                                s["weight"] if isinstance(s, dict) else s[2]
                            ),
                            "max_score": float(
                                s["max_score"] if isinstance(s, dict) else s[3]
                            ),
                        }
                    )
                cat_map.append(
                    {
                        "id": cat_id,
                        "name": cat["name"] if isinstance(cat, dict) else cat[1],
                        "weight": float(
                            cat["weight"] if isinstance(cat, dict) else cat[2]
                        ),
                        "subcategories": sub_list,
                    }
                )

            sub_ids = [s["id"] for c in cat_map for s in c["subcategories"]]
            assessments_by_sub = {}
            if sub_ids:
                fmt = ",".join(["%s"] * len(sub_ids))
                cur.execute(
                    f"SELECT id, subcategory_id, max_score FROM grade_assessments WHERE subcategory_id IN ({fmt})",
                    tuple(sub_ids),
                )
                for a in cur.fetchall():
                    aid = a["id"] if isinstance(a, dict) else a[0]
                    subid = a["subcategory_id"] if isinstance(a, dict) else a[1]
                    max_s = float(a["max_score"] if isinstance(a, dict) else a[2])
                    assessments_by_sub.setdefault(subid, []).append(
                        {"id": aid, "max_score": max_s}
                    )

            cur.execute(
                "SELECT student_id FROM student_classes WHERE class_id = %s",
                (class_id,),
            )
            students = [
                r["student_id"] if isinstance(r, dict) else r[0] for r in cur.fetchall()
            ]

            all_assessment_ids = [
                a["id"] for al in assessments_by_sub.values() for a in al
            ]
            scores_map = {}
            if all_assessment_ids and students:
                fmt_a = ",".join(["%s"] * len(all_assessment_ids))
                fmt_s = ",".join(["%s"] * len(students))
                query = f"SELECT assessment_id, student_id, score FROM student_scores WHERE assessment_id IN ({fmt_a}) AND student_id IN ({fmt_s})"
                cur.execute(query, tuple(all_assessment_ids) + tuple(students))
                for r in cur.fetchall():
                    aid = r["assessment_id"] if isinstance(r, dict) else r[0]
                    sid = r["student_id"] if isinstance(r, dict) else r[1]
                    sc = float(r["score"] if isinstance(r, dict) else r[2])
                    scores_map[(sid, aid)] = sc

            results = {}
            for student_id in students:
                final_pct = 0.0
                for cat in cat_map:
                    category_pct = 0.0
                    for sub in cat["subcategories"]:
                        assessments = assessments_by_sub.get(sub["id"], [])
                        sub_sum = 0.0
                        sub_max = 0.0
                        for a in assessments:
                            sub_sum += scores_map.get((student_id, a["id"]), 0.0)
                            sub_max += a["max_score"]
                        if sub_max == 0:
                            sub_pct = 0.0
                        else:
                            sub_pct = (sub_sum / sub_max) * 100.0
                        sub_contrib = sub_pct * (sub["weight"] / 100.0)
                        category_pct += sub_contrib
                    weighted_cat = category_pct * (cat["weight"] / 100.0)
                    final_pct += weighted_cat

                transmuted = final_pct * 0.625 + 37.5
                if transmuted < 75:
                    equiv = "5.0"
                elif transmuted < 77:
                    equiv = "3.0"
                elif transmuted < 80:
                    equiv = "2.75"
                elif transmuted < 83:
                    equiv = "2.5"
                elif transmuted < 86:
                    equiv = "2.25"
                elif transmuted < 89:
                    equiv = "2.0"
                elif transmuted < 92:
                    equiv = "1.75"
                elif transmuted < 95:
                    equiv = "1.5"
                else:
                    equiv = "1.25"

                results[student_id] = {
                    "final_percentage": round(final_pct, 4),
                    "transmuted": round(transmuted, 4),
                    "equivalent": equiv,
                }

        return jsonify(
            {"class_id": class_id, "structure_id": structure_id, "results": results}
        )
    except Exception as e:
        logger.exception(f"Failed to compute grades for class {class_id}: {e}")
        return jsonify({"error": str(e)}), 500


# Exempt this compute endpoint from CSRF to allow programmatic POSTs (tests/dev tools)
compute_class_grades.csrf_exempt = True
