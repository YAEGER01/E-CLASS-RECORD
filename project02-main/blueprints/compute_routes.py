from flask import Blueprint, jsonify, request
from utils.auth_utils import login_required
from utils.db_conn import get_db_connection

compute_bp = Blueprint("compute", __name__)


def _normalize_groups(groups: dict) -> dict:
    """Flatten raw payload groups into a consistent numeric structure."""
    norm_groups = {}
    for key, g in (groups or {}).items():
        try:
            ids = g.get("ids", []) if isinstance(g, dict) else []
            maxes = g.get("maxes", []) if isinstance(g, dict) else []
            maxTotal = (
                float(g.get("maxTotal", sum([float(m or 0) for m in (maxes or [])])))
                if g
                else 0.0
            )
            subweight = float(g.get("subweight", 0) or 0)
            ids = [int(x) for x in (ids or [])]
            norm_groups[key] = {
                "ids": ids,
                "maxes": [float(m or 0) for m in (maxes or [])],
                "maxTotal": float(maxTotal),
                "subweight": float(subweight),
            }
        except Exception:
            norm_groups[key] = {
                "ids": [],
                "maxes": [],
                "maxTotal": 0.0,
                "subweight": 0.0,
            }
    return norm_groups


def _compute_group_metrics(groups: dict, students: list):
    """Sum per-assessment scores and derive group-level totals/weights for each student."""
    norm_groups = _normalize_groups(groups)
    results = {}
    aggregates = {}

    for s in students:
        sid = int(s.get("student_id") or 0)
        rowscores = s.get("scores", {}) if isinstance(s, dict) else {}
        score_map = {}
        for k, v in (rowscores or {}).items():
            try:
                score_map[int(k)] = None if v is None else float(v)
            except Exception:
                continue

        stud_res = {}
        category_totals = {}
        category_weighted_raw = {}

        for gkey, g in norm_groups.items():
            ids = g.get("ids", [])
            maxTotal = float(g.get("maxTotal") or 0.0)
            subweight = float(g.get("subweight") or 0.0)
            total = 0.0
            for aid in ids:
                v = score_map.get(aid)
                if v is None:
                    continue
                try:
                    total += float(v)
                except Exception:
                    continue
            eq_pct = (
                (float(total) / float(maxTotal) * 100.0)
                if maxTotal and maxTotal > 0
                else 0.0
            )
            reqpct_raw = (eq_pct * subweight) / 100.0 if subweight else 0.0
            reqpct = round(reqpct_raw, 2)
            stud_res[gkey] = {
                "total": round(total, 2),
                "eq_pct": round(eq_pct, 2),
                "reqpct": reqpct,
                "reqpct_display": round(reqpct, 2),
            }

            cat_label = (gkey.split("::", 1)[0] or "").strip().upper()
            if cat_label:
                # Track both the raw totals (for transparency) and the weighted contribution used by formulas
                category_totals[cat_label] = category_totals.get(cat_label, 0.0) + total
                category_weighted_raw[cat_label] = (
                    category_weighted_raw.get(cat_label, 0.0) + reqpct_raw
                )

        sid_key = str(sid)
        results[sid_key] = stud_res
        aggregates[sid_key] = {
            "category_totals": category_totals,
            "category_weighted_raw": category_weighted_raw,
        }

    return results, aggregates


def compute_major_grade(groups: dict, students: list) -> dict:
    """Return MAJOR-class group metrics (mirrors historical behaviour)."""
    results, _ = _compute_group_metrics(groups, students)
    return results


def _map_minor_equivalent(score: float) -> str:
    """Translate a MINOR final grade into the transmuted equivalent scale."""
    if score < 75:
        return "5.0"
    if score < 77:
        return "3.0"
    if score < 80:
        return "2.75"
    if score < 83:
        return "2.50"
    if score < 86:
        return "2.25"
    if score < 89:
        return "2.00"
    if score < 92:
        return "1.75"
    if score < 95:
        return "1.50"
    return "1.25"


def compute_minor_grade(groups: dict, students: list) -> tuple[dict, dict]:
    """Produce MINOR-class group metrics plus lecture/lab/overall summary figures."""
    results, aggregates = _compute_group_metrics(groups, students)
    summaries = {}

    for sid, agg in aggregates.items():
        weighted_raw = agg.get("category_weighted_raw", {}) or {}
        lecture_raw = weighted_raw.get("LECTURE", 0.0)
        laboratory_raw = weighted_raw.get("LABORATORY", 0.0)
        initial_grade_raw = sum(weighted_raw.values())
        # Spreadsheet logic: 50% lecture + 50% laboratory + base 50 transmutation
        final_grade = round(initial_grade_raw * 0.5 + 50, 2)
        summaries[sid] = {
            "lecture": round(lecture_raw, 2),
            "laboratory": round(laboratory_raw, 2),
            "initial_grade": round(initial_grade_raw, 2),
            "final_grade": final_grade,
            "equivalent": _map_minor_equivalent(final_grade),
        }

    return results, summaries


def _resolve_class_type(class_id) -> str:
    """Look up class_type from the DB, defaulting to MAJOR for unknown classes."""
    default_type = "MAJOR"
    if not class_id:
        return default_type
    try:
        with get_db_connection().cursor() as cursor:
            cursor.execute(
                "SELECT class_type FROM classes WHERE id = %s",
                (int(class_id),),
            )
            row = cursor.fetchone()
    except Exception:
        return default_type

    if not row:
        return default_type
    class_type = row["class_type"] if isinstance(row, dict) else row[0]
    return (class_type or default_type).upper()


@compute_bp.route("/api/grade-entry/compute", methods=["POST"])
@login_required
def api_grade_entry_compute():
    """
    Compute derived values for grade-entry page.

    Expected JSON shape:
    {
      "class_id": 123,
      "groups": {
         "LECTURE::Quiz": { "ids": [11,12], "maxes": [10,20], "maxTotal":30, "subweight": 20 },
         ...
      },
      "students": [
         { "student_id": 1, "scores": { "11": 8, "12": null } },
         ...
      ]
    }

    Returns JSON:
    {
      "results": {
         "1": { "LECTURE::Quiz": { "total": 8.0, "eq_pct": 26.67, "reqpct": 5.33 }, ... },
         ...
      }
    }
    """
    try:
        data = request.get_json(force=True) or {}
        # Backwards-compatible single-shot total: { scores: [number,...] }
        if "scores" in data and isinstance(data.get("scores"), list):
            try:
                total = sum(
                    float(s)
                    for s in data.get("scores", [])
                    if isinstance(s, (int, float, str))
                    and str(s).replace(".", "", 1).replace("-", "", 1).isdigit()
                )
            except Exception:
                total = 0.0
            return jsonify({"TOTAL": round(float(total), 2)}), 200

        groups = data.get("groups", {})
        students = data.get("students", [])

        if not isinstance(groups, dict):
            return jsonify({"error": "groups must be an object"}), 400
        if not isinstance(students, list):
            return jsonify({"error": "students must be a list"}), 400

        grade_type = _resolve_class_type(data.get("class_id"))
        if grade_type == "MINOR":
            results, summaries = compute_minor_grade(groups, students)
            payload = {"results": results}
            if summaries:
                payload["summaries"] = summaries
            return jsonify(payload), 200

        results = compute_major_grade(groups, students)
        return jsonify({"results": results}), 200
    except Exception as exc:
        # Return generic error but include message for dev debugging
        return jsonify({"error": "failed_to_compute", "message": str(exc)}), 500
