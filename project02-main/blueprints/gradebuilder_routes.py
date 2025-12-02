import json
import logging
from datetime import datetime
from typing import Optional, Tuple

from flask import Blueprint, jsonify, request, session
from flask_wtf.csrf import generate_csrf

from utils.db_conn import get_db_connection
from utils.auth_utils import login_required

logger = logging.getLogger(__name__)


gradebuilder_bp = Blueprint("gradebuilder", __name__)


def _current_instructor_id() -> Optional[int]:
    try:
        user_id = session.get("user_id")
        if not user_id:
            return None
        with get_db_connection().cursor() as cursor:
            cursor.execute("SELECT id FROM instructors WHERE user_id = %s", (user_id,))
            row = cursor.fetchone()
            return row["id"] if isinstance(row, dict) else (row[0] if row else None)
    except Exception:
        return None


def _instructor_owns_class(class_id: int, instructor_id: int) -> bool:
    try:
        with get_db_connection().cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM classes WHERE id = %s AND instructor_id = %s",
                (class_id, instructor_id),
            )
            return cursor.fetchone() is not None
    except Exception:
        return False


def _get_instructor_profile(instructor_id: int):
    try:
        with get_db_connection().cursor() as cursor:
            cursor.execute(
                """
                SELECT u.email,
                       COALESCE(CONCAT(pi.first_name, ' ', pi.last_name), u.school_id) AS name
                FROM instructors i
                JOIN users u ON i.user_id = u.id
                LEFT JOIN personal_info pi ON u.personal_info_id = pi.id
                WHERE i.id = %s
                """,
                (instructor_id,),
            )
            row = cursor.fetchone() or {}
            return {
                "id": instructor_id,
                "name": row.get("name") if isinstance(row, dict) else None,
                "email": row.get("email") if isinstance(row, dict) else None,
            }
    except Exception:
        return {"id": instructor_id}


# GET /api/gradebuilder/data — classes + saved structures + csrf token
@gradebuilder_bp.route(
    "/api/gradebuilder/data", methods=["GET"], endpoint="gb_get_data"
)
@login_required
def gb_get_data():
    instructor_id = _current_instructor_id()
    if not instructor_id:
        return jsonify({"error": "access_denied"}), 403

    try:
        with get_db_connection().cursor() as cursor:
            # classes owned by instructor
            cursor.execute(
                """
                SELECT id AS class_id, course, section, track, class_type
                FROM classes
                WHERE instructor_id = %s
                ORDER BY created_at DESC, id DESC
                """,
                (instructor_id,),
            )
            classes = cursor.fetchall() or []

            class_ids = [
                c["class_id"] if isinstance(c, dict) else c[0] for c in classes
            ]
            structures = []
            if class_ids:
                placeholders = ",".join(["%s"] * len(class_ids))
                cursor.execute(
                    f"""
                    SELECT id,
                           class_id,
                           structure_name,
                           structure_json,
                           version,
                           is_active,
                           created_at,
                           updated_at
                    FROM grade_structures
                    WHERE class_id IN ({placeholders})
                    ORDER BY updated_at DESC, id DESC
                    """,
                    tuple(class_ids),
                )
                structures = cursor.fetchall() or []

        csrf_token = generate_csrf()
        instructor = _get_instructor_profile(instructor_id)
        return (
            jsonify(
                {
                    "csrf_token": csrf_token,
                    "instructor": instructor,
                    "classes": classes,
                    "structures": structures,
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Failed to fetch gradebuilder data: {str(e)}")
        return jsonify({"error": "failed_to_fetch"}), 500


# Helper: validate structure JSON (lightweight)
def _validate_structure(structure: dict) -> Tuple[bool, list]:
    errors = []
    if not isinstance(structure, dict):
        return False, ["structure_json must be an object"]
    for key in ("LABORATORY", "LECTURE"):
        if key not in structure:
            # allow empty categories, but must exist
            errors.append(f"Missing required key: {key}")
            continue
        items = structure.get(key)
        if items is None:
            structure[key] = []
            items = []
        if not isinstance(items, list):
            errors.append(f"{key} must be an array")
            continue
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append(f"{key}[{i}] must be an object")
                continue
            name = item.get("name")
            weight = item.get("weight")
            if not isinstance(name, str) or not name.strip():
                errors.append(f"{key}[{i}].name must be a non-empty string")
            try:
                float(weight)
            except Exception:
                errors.append(f"{key}[{i}].weight must be a number")
    # per-category total must be ~100 if non-empty
    for key in ("LABORATORY", "LECTURE"):
        items = structure.get(key) or []
        if items:
            try:
                total = sum(float((it or {}).get("weight") or 0) for it in items)
                if abs(total - 100.0) > 0.01:
                    errors.append(
                        f"{key} subcategory weights must sum to 100 (got {total})"
                    )
            except Exception:
                # ignore, individual item errors already captured
                pass
    return (len(errors) == 0), errors


# POST /api/gradebuilder/save — create a new versioned structure (activates it)
@gradebuilder_bp.route("/api/gradebuilder/save", methods=["POST"], endpoint="gb_save")
@login_required
def gb_save():
    instructor_id = _current_instructor_id()
    if not instructor_id:
        return jsonify({"error": "access_denied"}), 403

    try:
        payload = request.get_json(force=True, silent=True) or {}
        class_id = payload.get("class_id")
        structure_name = (payload.get("structure_name") or "Untitled").strip()
        structure_json = payload.get("structure_json")

        try:
            class_id = int(class_id)
        except Exception:
            return jsonify({"error": "invalid_class_id"}), 400

        if not _instructor_owns_class(class_id, instructor_id):
            return jsonify({"error": "access_denied"}), 403

        # structure_json may arrive as stringified JSON; accept dict or str
        if isinstance(structure_json, str):
            try:
                structure_obj = json.loads(structure_json)
            except Exception:
                return jsonify({"error": "invalid_structure_json"}), 400
        elif isinstance(structure_json, dict):
            structure_obj = structure_json
        else:
            return jsonify({"error": "invalid_structure_json"}), 400

        ok, errs = _validate_structure(structure_obj)
        if not ok:
            return jsonify({"error": "validation_failed", "details": errs}), 400

        structure_json_str = json.dumps(structure_obj)

        # All DB operations must be inside the cursor block
        with get_db_connection().cursor() as cursor:
            # compute next version
            cursor.execute(
                "SELECT COALESCE(MAX(version), 0) + 1 AS v FROM grade_structures WHERE class_id = %s",
                (class_id,),
            )
            row = cursor.fetchone()
            next_version = (row["v"] if isinstance(row, dict) else row[0]) or 1

            # optionally deactivate previous active structure
            try:
                cursor.execute(
                    "UPDATE grade_structures SET is_active = 0, updated_at = NOW() WHERE class_id = %s AND is_active = 1",
                    (class_id,),
                )
            except Exception:
                pass

            # insert new record as active (created_by is required by schema)
            cursor.execute(
                """
                INSERT INTO grade_structures (class_id, structure_name, structure_json, created_by, version, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, 1, NOW(), NOW())
                """,
                (
                    class_id,
                    structure_name,
                    structure_json_str,
                    instructor_id,
                    next_version,
                ),
            )
            new_id = getattr(cursor, "lastrowid", None)
            if not new_id:
                cursor.execute(
                    "SELECT id FROM grade_structures WHERE class_id = %s ORDER BY updated_at DESC, id DESC LIMIT 1",
                    (class_id,),
                )
                r2 = cursor.fetchone()
                new_id = r2["id"] if isinstance(r2, dict) else (r2[0] if r2 else None)

            # --- Normalize and insert categories/subcategories ---
            cursor.execute(
                "SELECT id FROM grade_categories WHERE structure_id = %s", (new_id,)
            )
            cat_rows = cursor.fetchall() or []
            cat_ids = [r["id"] if isinstance(r, dict) else r[0] for r in cat_rows]
            if cat_ids:
                placeholders = ",".join(["%s"] * len(cat_ids))
                cursor.execute(
                    f"DELETE FROM grade_subcategories WHERE category_id IN ({placeholders})",
                    tuple(cat_ids),
                )
                cursor.execute(
                    "DELETE FROM grade_categories WHERE structure_id = %s", (new_id,)
                )

            struct = structure_obj
            pos_cat = 1
            for cat_key in ("LECTURE", "LABORATORY"):
                subs = struct.get(cat_key) or []
                if subs:
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
                        (new_id, cat_key, cat_weight, pos_cat),
                    )
                    cat_id = cursor.lastrowid
                    pos_sub = 1
                    for s in subs:
                        sub_name = s.get("name")
                        sub_weight = s.get("weight") or 0
                        cursor.execute(
                            """
                            INSERT INTO grade_subcategories (category_id, name, weight, max_score, passing_score, position, description)
                            VALUES (%s, %s, %s, %s, NULL, %s, NULL)
                            """,
                            (cat_id, sub_name, float(sub_weight), 100.0, pos_sub),
                        )
                        pos_sub += 1
                    pos_cat += 1

            # Commit transaction
            try:
                get_db_connection().commit()
            except Exception:
                logger.warning("Commit failed after save; attempting to continue")

        return jsonify({"message": "saved", "id": new_id, "version": next_version}), 200
    except Exception as e:
        logger.error(f"Failed to save grade structure: {str(e)}")
        return jsonify({"error": "failed_to_save"}), 500


# GET /api/gradebuilder/history/<id> — list versions for the same class
@gradebuilder_bp.route(
    "/api/gradebuilder/history/<int:structure_id>",
    methods=["GET"],
    endpoint="gb_history",
)
@login_required
def gb_history(structure_id: int):
    instructor_id = _current_instructor_id()
    if not instructor_id:
        return jsonify({"error": "access_denied"}), 403

    try:
        with get_db_connection().cursor() as cursor:
            cursor.execute(
                "SELECT class_id FROM grade_structures WHERE id = %s",
                (structure_id,),
            )
            row = cursor.fetchone()
            if not row:
                return jsonify({"error": "not_found"}), 404
            class_id = row["class_id"] if isinstance(row, dict) else row[0]
            if not _instructor_owns_class(class_id, instructor_id):
                return jsonify({"error": "access_denied"}), 403

            cursor.execute(
                """
                SELECT id, class_id, structure_name, structure_json, version, is_active, created_at, updated_at
                FROM grade_structures
                WHERE class_id = %s
                ORDER BY version DESC, updated_at DESC
                """,
                (class_id,),
            )
            history = cursor.fetchall() or []
        return jsonify({"class_id": class_id, "history": history})
    except Exception as e:
        logger.error(f"Failed to fetch history for {structure_id}: {str(e)}")
        return jsonify({"error": "failed_to_fetch_history"}), 500


# DELETE /api/gradebuilder/delete/<id> — remove a structure version
@gradebuilder_bp.route(
    "/api/gradebuilder/delete/<int:structure_id>",
    methods=["DELETE"],
    endpoint="gb_delete",
)
@login_required
def gb_delete(structure_id: int):
    instructor_id = _current_instructor_id()
    if not instructor_id:
        return jsonify({"error": "access_denied"}), 403

    try:
        with get_db_connection().cursor() as cursor:
            cursor.execute(
                "SELECT class_id, is_active FROM grade_structures WHERE id = %s",
                (structure_id,),
            )
            row = cursor.fetchone()
            if not row:
                return jsonify({"error": "not_found"}), 404
            class_id = row["class_id"] if isinstance(row, dict) else row[0]
            is_active = row["is_active"] if isinstance(row, dict) else row[1]

            if not _instructor_owns_class(class_id, instructor_id):
                return jsonify({"error": "access_denied"}), 403

            cursor.execute(
                "DELETE FROM grade_structures WHERE id = %s", (structure_id,)
            )

            message = "deleted"
            # Optional: if we deleted the active structure, there may now be no active version
            # We will not auto-activate an older one here to avoid surprises.
        # commit deletion
        try:
            get_db_connection().commit()
        except Exception:
            logger.warning("Commit failed after delete; attempting to continue")
        return jsonify({"message": message})
    except Exception as e:
        logger.error(f"Failed to delete structure {structure_id}: {str(e)}")
        return jsonify({"error": "failed_to_delete"}), 500


# POST /api/gradebuilder/update/<id> — update an existing structure in place
@gradebuilder_bp.route(
    "/api/gradebuilder/update/<int:structure_id>",
    methods=["POST"],
    endpoint="gb_update",
)
@login_required
def gb_update(structure_id: int):
    instructor_id = _current_instructor_id()
    if not instructor_id:
        return jsonify({"error": "access_denied"}), 403

    try:
        payload = request.get_json(force=True, silent=True) or {}
        structure_name = (payload.get("structure_name") or "Untitled").strip()
        structure_json = payload.get("structure_json")

        # resolve class and ownership
        with get_db_connection().cursor() as cursor:
            cursor.execute(
                "SELECT class_id FROM grade_structures WHERE id = %s",
                (structure_id,),
            )
            row = cursor.fetchone()
            if not row:
                return jsonify({"error": "not_found"}), 404
            class_id = row["class_id"] if isinstance(row, dict) else row[0]
            if not _instructor_owns_class(class_id, instructor_id):
                return jsonify({"error": "access_denied"}), 403

        # parse structure
        if isinstance(structure_json, str):
            try:
                structure_obj = json.loads(structure_json)
            except Exception:
                return jsonify({"error": "invalid_structure_json"}), 400
        elif isinstance(structure_json, dict):
            structure_obj = structure_json
        else:
            return jsonify({"error": "invalid_structure_json"}), 400

        ok, errs = _validate_structure(structure_obj)
        if not ok:
            return jsonify({"error": "validation_failed", "details": errs}), 400

        structure_json_str = json.dumps(structure_obj)

        # update in place and normalize categories/subcategories
        with get_db_connection().cursor() as cursor:
            cursor.execute(
                """
                UPDATE grade_structures
                SET structure_name = %s,
                    structure_json = %s,
                    updated_at = NOW()
                WHERE id = %s
                """,
                (structure_name, structure_json_str, structure_id),
            )

            # Remove ALL previous categories/subcategories for this structure
            cursor.execute(
                "SELECT id FROM grade_categories WHERE structure_id = %s",
                (structure_id,),
            )
            cat_rows = cursor.fetchall() or []
            cat_ids = [r["id"] if isinstance(r, dict) else r[0] for r in cat_rows]
            if cat_ids:
                placeholders = ",".join(["%s"] * len(cat_ids))
                cursor.execute(
                    f"DELETE FROM grade_subcategories WHERE category_id IN ({placeholders})",
                    tuple(cat_ids),
                )
            cursor.execute(
                "DELETE FROM grade_categories WHERE structure_id = %s", (structure_id,)
            )

            # Parse the structure JSON and re-insert ALL categories/subcategories
            struct = structure_obj
            pos_cat = 1
            for cat_key in ("LABORATORY", "LECTURE"):
                subs = struct.get(cat_key)
                # Always insert the category, even if subs is empty or None
                cat_weight = 0.0
                for s in subs or []:
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
                pos_sub = 1
                for s in subs or []:
                    sub_name = s.get("name")
                    sub_weight = s.get("weight") or 0
                    cursor.execute(
                        """
                        INSERT INTO grade_subcategories (category_id, name, weight, max_score, passing_score, position, description)
                        VALUES (%s, %s, %s, %s, NULL, %s, NULL)
                        """,
                        (cat_id, sub_name, float(sub_weight), 100.0, pos_sub),
                    )
                    pos_sub += 1
                pos_cat += 1

        try:
            get_db_connection().commit()
        except Exception:
            logger.warning("Commit failed after update; attempting to continue")

        return jsonify({"message": "updated", "id": structure_id}), 200
    except Exception as e:
        logger.error(f"Failed to update grade structure {structure_id}: {str(e)}")
        return jsonify({"error": "failed_to_update"}), 500
