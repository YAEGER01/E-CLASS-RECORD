import json
import logging
from flask import Blueprint, request, jsonify, session
from utils.db_conn import get_db_connection

logger = logging.getLogger(__name__)


assessments_bp = Blueprint("assessments", __name__)


def _require_instructor():
    """Local instructor auth helper to avoid circular imports.
    Returns (instructor_id, error_response_or_None)
    """
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


@assessments_bp.route("/api/assessments", methods=["GET"])
def api_list_assessments():
    """List assessments. Query params: class_id or structure_id or subcategory name."""
    instructor_id, err = _require_instructor()
    if err:
        return err

    class_id = request.args.get("class_id")
    structure_id = request.args.get("structure_id")
    subcategory = request.args.get("subcategory")

    # Join through subcategory -> category -> structure to resolve class/structure linkage
    q = (
        "SELECT ga.id, ga.name, ga.max_score, ga.subcategory_id, ga.created_at, gs.class_id "
        "FROM grade_assessments ga "
        "JOIN grade_subcategories gsc ON ga.subcategory_id = gsc.id "
        "JOIN grade_categories gc ON gsc.category_id = gc.id "
        "JOIN grade_structures gs ON gc.structure_id = gs.id"
    )
    clauses = []
    params = []
    if class_id:
        clauses.append("gs.class_id = %s")
        params.append(int(class_id))
    if structure_id:
        clauses.append("gc.structure_id = %s")
        params.append(int(structure_id))
    if subcategory:
        clauses.append("gsc.name = %s")
        params.append(subcategory)

    if clauses:
        q += " WHERE " + " AND ".join(clauses)

    try:
        with get_db_connection().cursor() as cursor:
            cursor.execute(q, tuple(params))
            rows = cursor.fetchall()
        return jsonify({"assessments": rows}), 200
    except Exception as e:
        logger.error(f"Failed to list assessments: {str(e)}")
        return jsonify({"error": "failed_to_list_assessments"}), 500


@assessments_bp.route("/api/assessments", methods=["POST"])
def api_create_assessment():
    instructor_id, err = _require_instructor()
    if err:
        return err
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    class_id = data.get(
        "class_id"
    )  # optional; not stored in table but may be used for auth checks later
    structure_id = data.get("structure_id")
    subcategory = data.get("subcategory")  # subcategory name (string)
    category = data.get("category")  # optional, helps disambiguate
    max_score = data.get("max_score")
    assessment_date = data.get("assessment_date")

    # Be liberal in what we accept: allow structure_id OR class_id (we'll resolve active structure)
    if not name or not subcategory or max_score is None:
        return jsonify({"error": "invalid_payload", "reason": "missing_fields"}), 400

    # Normalize inputs
    try:
        structure_id_int = (
            int(structure_id) if structure_id not in (None, "", "None") else None
        )
    except Exception:
        structure_id_int = None
    try:
        class_id_int = int(class_id) if class_id not in (None, "", "None") else None
    except Exception:
        class_id_int = None

    # Resolve structure if not provided
    if not structure_id_int and class_id_int:
        try:
            with get_db_connection().cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM grade_structures WHERE class_id = %s AND is_active = 1 ORDER BY updated_at DESC, id DESC LIMIT 1",
                    (class_id_int,),
                )
                row = cursor.fetchone()
                structure_id_int = row["id"] if row else None
        except Exception:
            structure_id_int = None

    if not structure_id_int:
        return (
            jsonify({"error": "invalid_payload", "reason": "structure_id_unresolved"}),
            400,
        )

    try:
        with get_db_connection().cursor() as cursor:
            # Ensure relational structure (grade_categories/subcategories) exists for this structure
            def _materialize_structure_if_needed(cur, structure_id_val: int):
                # If categories already exist for this structure, nothing to do
                cur.execute(
                    "SELECT COUNT(1) AS cnt FROM grade_categories WHERE structure_id = %s",
                    (structure_id_val,),
                )
                if (cur.fetchone() or {}).get("cnt", 0) > 0:
                    return

                # Load structure JSON
                cur.execute(
                    "SELECT structure_json FROM grade_structures WHERE id = %s",
                    (structure_id_val,),
                )
                row_js = cur.fetchone()
                if not row_js or not row_js.get("structure_json"):
                    raise ValueError("structure_json_missing")
                try:
                    struct = json.loads(row_js["structure_json"]) or {}
                except Exception:
                    raise ValueError("structure_json_invalid")

                # Helper: insert category and its subcategories
                def insert_cat(cat_name: str, subs: list, position_start: int):
                    # Category weight: sum of sub weights (fallback 0)
                    cat_weight = 0.0
                    for s in subs or []:
                        try:
                            cat_weight += float(s.get("weight") or 0)
                        except Exception:
                            pass
                    cur.execute(
                        """
                        INSERT INTO grade_categories (structure_id, name, weight, position, description)
                        VALUES (%s, %s, %s, %s, NULL)
                        """,
                        (structure_id_val, cat_name, cat_weight, position_start),
                    )
                    cat_id = cur.lastrowid
                    # Insert subcategories
                    pos = 1
                    for s in subs or []:
                        sub_name = s.get("name")
                        sub_weight = s.get("weight") or 0
                        # The schema requires max_score NOT NULL; default to 100
                        cur.execute(
                            """
                            INSERT INTO grade_subcategories (category_id, name, weight, max_score, passing_score, position, description)
                            VALUES (%s, %s, %s, %s, NULL, %s, NULL)
                            """,
                            (cat_id, sub_name, float(sub_weight), 100.0, pos),
                        )
                        pos += 1
                    return position_start + 1

                # Insert categories in fixed order for consistency
                pos_cat = 1
                for cat_key in ("LECTURE", "LABORATORY"):
                    subs = struct.get(cat_key) or []
                    if subs:
                        pos_cat = insert_cat(cat_key, subs, pos_cat)

            _materialize_structure_if_needed(cursor, structure_id_int)
            # Resolve subcategory_id from structure and subcategory name
            params = [int(structure_id_int), subcategory]
            cat_filter = ""
            if category:
                cat_filter = " AND gc.name = %s"
                params.append(category)
            cursor.execute(
                f"""
                SELECT gsc.id AS subcategory_id
                FROM grade_subcategories gsc
                JOIN grade_categories gc ON gsc.category_id = gc.id
                WHERE gc.structure_id = %s AND gsc.name = %s{cat_filter}
                LIMIT 1
                """,
                tuple(params),
            )
            row = cursor.fetchone()
            if not row:
                return jsonify({"error": "subcategory_not_found"}), 404
            subcategory_id = row["subcategory_id"]

            # Determine next position within the subcategory
            cursor.execute(
                "SELECT COALESCE(MAX(position), 0) + 1 AS next_pos FROM grade_assessments WHERE subcategory_id = %s",
                (subcategory_id,),
            )
            next_pos = (cursor.fetchone() or {}).get("next_pos", 1)

            # Insert new assessment
            cursor.execute(
                """
                INSERT INTO grade_assessments (subcategory_id, name, weight, max_score, passing_score, position, description)
                VALUES (%s, %s, NULL, %s, NULL, %s, NULL)
                """,
                (subcategory_id, name, float(max_score), int(next_pos)),
            )
            aid = cursor.lastrowid
        get_db_connection().commit()
        return jsonify({"success": True, "assessment_id": aid}), 201
    except Exception as e:
        get_db_connection().rollback()
        logger.error(f"Failed to create assessment: {str(e)}")
        return jsonify({"error": "failed_to_create_assessment"}), 500


@assessments_bp.route("/api/assessments/<int:assessment_id>", methods=["PUT"])
def api_update_assessment(assessment_id):
    instructor_id, err = _require_instructor()
    if err:
        return err
    data = request.get_json() or {}
    fields = []
    params = []
    for f in ("name", "max_score", "subcategory", "assessment_date"):
        if f in data:
            fields.append(f + " = %s")
            params.append(data[f])
    if not fields:
        return jsonify({"error": "no_fields"}), 400
    params.extend([assessment_id])
    try:
        with get_db_connection().cursor() as cursor:
            cursor.execute(
                f"UPDATE grade_assessments SET {', '.join(fields)} WHERE id = %s",
                tuple(params),
            )
            if cursor.rowcount == 0:
                return jsonify({"error": "not_found"}), 404
        get_db_connection().commit()
        return jsonify({"success": True}), 200
    except Exception as e:
        get_db_connection().rollback()
        logger.error(f"Failed to update assessment: {str(e)}")
        return jsonify({"error": "failed_to_update"}), 500


@assessments_bp.route("/api/assessments/<int:assessment_id>", methods=["DELETE"])
def api_delete_assessment(assessment_id):
    instructor_id, err = _require_instructor()
    if err:
        return err
    try:
        with get_db_connection().cursor() as cursor:
            cursor.execute(
                "DELETE FROM grade_assessments WHERE id = %s", (assessment_id,)
            )
            if cursor.rowcount == 0:
                return jsonify({"error": "not_found"}), 404
        get_db_connection().commit()
        return jsonify({"success": True}), 200
    except Exception as e:
        get_db_connection().rollback()
        logger.error(f"Failed to delete assessment: {str(e)}")
        return jsonify({"error": "failed_to_delete"}), 500


@assessments_bp.route("/api/assessments/simple", methods=["POST"])
def api_create_assessment_simple():
    """
    More permissive creator for assessments that accepts either JSON or form data.
    Accepts fields:
      - name (or assessment_name)
      - max_score (or max)
      - subcategory_id (optional)
      - structure_id (optional)
      - class_id (optional)
      - category (optional, helps disambiguate when resolving by name)
      - subcategory (optional when subcategory_id provided)

    Strategy:
      1) If subcategory_id provided -> use it directly.
      2) Else resolve subcategory_id via (structure_id or class_id) + (subcategory and optional category).
      3) Insert into grade_assessments with next position.
    """
    instructor_id, err = _require_instructor()
    if err:
        return err

    # Accept JSON or form
    if request.is_json:
        data = request.get_json(silent=True) or {}
    else:
        data = request.form.to_dict(flat=True)

    name = data.get("name") or data.get("assessment_name")
    category = data.get("category")
    subcategory = data.get("subcategory")
    subcategory_id = data.get("subcategory_id")
    structure_id = data.get("structure_id") or data.get("structure")
    class_id = data.get("class_id")
    max_score = data.get("max_score") or data.get("max")

    # Coerce numerics when present
    def _to_int(val):
        try:
            return int(val) if val not in (None, "", "None") else None
        except Exception:
            return None

    def _to_float(val):
        try:
            return float(val)
        except Exception:
            return None

    subcategory_id = _to_int(subcategory_id)
    structure_id = _to_int(structure_id)
    class_id = _to_int(class_id)
    max_score = _to_float(max_score)

    if not name or max_score is None or max_score <= 0:
        return (
            jsonify(
                {"error": "invalid_payload", "reason": "missing_or_invalid_fields"}
            ),
            400,
        )

    # Resolve structure if only class_id provided
    if not structure_id and class_id:
        try:
            with get_db_connection().cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM grade_structures WHERE class_id = %s AND is_active = 1 ORDER BY updated_at DESC, id DESC LIMIT 1",
                    (class_id,),
                )
                r = cursor.fetchone()
                structure_id = r["id"] if r else None
        except Exception:
            structure_id = None

    if not subcategory_id:
        # Need subcategory name to resolve
        if not subcategory:
            return (
                jsonify({"error": "invalid_payload", "reason": "subcategory_required"}),
                400,
            )
        # Resolve subcategory_id from structure + names
        if not structure_id:
            return (
                jsonify(
                    {"error": "invalid_payload", "reason": "structure_id_unresolved"}
                ),
                400,
            )
        try:
            with get_db_connection().cursor() as cursor:
                params = [structure_id, subcategory]
                cat_filter = ""
                if category:
                    cat_filter = " AND gc.name = %s"
                    params.append(category)
                cursor.execute(
                    f"""
                    SELECT gsc.id AS subcategory_id
                    FROM grade_subcategories gsc
                    JOIN grade_categories gc ON gsc.category_id = gc.id
                    WHERE gc.structure_id = %s AND gsc.name = %s{cat_filter}
                    LIMIT 1
                    """,
                    tuple(params),
                )
                row = cursor.fetchone()
                if not row:
                    # Attempt to materialize relational rows from structure JSON if none exist yet
                    cursor.execute(
                        "SELECT COUNT(1) AS cnt FROM grade_categories WHERE structure_id = %s",
                        (structure_id,),
                    )
                    if (cursor.fetchone() or {}).get("cnt", 0) == 0:
                        # Load structure JSON
                        cursor.execute(
                            "SELECT structure_json FROM grade_structures WHERE id = %s",
                            (structure_id,),
                        )
                        row_js = cursor.fetchone()
                        if not row_js or not row_js.get("structure_json"):
                            return jsonify({"error": "structure_json_missing"}), 400
                        try:
                            struct = json.loads(row_js["structure_json"]) or {}
                        except Exception:
                            return jsonify({"error": "structure_json_invalid"}), 400

                        # Insert categories and their subcategories
                        pos_cat = 1
                        for cat_key in ("LECTURE", "LABORATORY"):
                            subs = struct.get(cat_key) or []
                            if not subs:
                                continue
                            # Category weight as sum of sub weights
                            cat_weight = 0.0
                            for s in subs:
                                try:
                                    cat_weight += float(s.get("weight") or 0)
                                except Exception:
                                    pass
                            cursor.execute(
                                """
                                INSERT INTO grade_categories (structure_id, name, weight, position, description)
                                VALUES (%s, %s, %s, %s, NULL)
                                """,
                                (structure_id, cat_key, cat_weight, pos_cat),
                            )
                            cat_id = cursor.lastrowid
                            # insert subcategories
                            pos_sub = 1
                            for s in subs:
                                sub_name = s.get("name")
                                sub_weight = s.get("weight") or 0
                                cursor.execute(
                                    """
                                    INSERT INTO grade_subcategories (category_id, name, weight, max_score, passing_score, position, description)
                                    VALUES (%s, %s, %s, %s, NULL, %s, NULL)
                                    """,
                                    (
                                        cat_id,
                                        sub_name,
                                        float(sub_weight),
                                        100.0,
                                        pos_sub,
                                    ),
                                )
                                pos_sub += 1
                            pos_cat += 1

                        # Retry resolution after materialization
                        params = [structure_id, subcategory]
                        cat_filter = ""
                        if category:
                            cat_filter = " AND gc.name = %s"
                            params.append(category)
                        cursor.execute(
                            f"""
                            SELECT gsc.id AS subcategory_id
                            FROM grade_subcategories gsc
                            JOIN grade_categories gc ON gsc.category_id = gc.id
                            WHERE gc.structure_id = %s AND gsc.name = %s{cat_filter}
                            LIMIT 1
                            """,
                            tuple(params),
                        )
                        row = cursor.fetchone()

                if not row:
                    return jsonify({"error": "subcategory_not_found"}), 404
                subcategory_id = row["subcategory_id"]
        except Exception as e:
            logger.error(f"Failed to resolve subcategory: {str(e)}")
            return jsonify({"error": "failed_to_resolve_subcategory"}), 500

    try:
        with get_db_connection().cursor() as cursor:
            # Determine next position within the subcategory
            cursor.execute(
                "SELECT COALESCE(MAX(position), 0) + 1 AS next_pos FROM grade_assessments WHERE subcategory_id = %s",
                (subcategory_id,),
            )
            next_pos = (cursor.fetchone() or {}).get("next_pos", 1)

            # Insert into grade_assessments directly
            cursor.execute(
                """
                INSERT INTO grade_assessments (subcategory_id, name, weight, max_score, passing_score, position, description)
                VALUES (%s, %s, NULL, %s, NULL, %s, NULL)
                """,
                (subcategory_id, name, float(max_score), int(next_pos)),
            )
            aid = cursor.lastrowid
        get_db_connection().commit()
        return jsonify({"success": True, "assessment_id": aid}), 201
    except Exception as e:
        get_db_connection().rollback()
        logger.error(f"Failed to create assessment (simple): {str(e)}")
        return jsonify({"error": "failed_to_create_assessment"}), 500
