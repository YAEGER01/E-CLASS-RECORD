from flask import Blueprint, jsonify, request
from utils.auth_utils import login_required

compute_bp = Blueprint("compute", __name__)


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

        # Normalize groups: ensure maxTotal and ids are lists
        norm_groups = {}
        for key, g in groups.items():
            try:
                ids = g.get("ids", []) if isinstance(g, dict) else []
                maxes = g.get("maxes", []) if isinstance(g, dict) else []
                maxTotal = (
                    float(
                        g.get("maxTotal", sum([float(m or 0) for m in (maxes or [])]))
                    )
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

        results = {}
        for s in students:
            sid = int(s.get("student_id") or 0)
            rowscores = s.get("scores", {}) if isinstance(s, dict) else {}
            # Convert scores mapping keys to int
            score_map = {}
            for k, v in (rowscores or {}).items():
                try:
                    score_map[int(k)] = None if v is None else float(v)
                except Exception:
                    continue

            stud_res = {}
            for gkey, g in norm_groups.items():
                ids = g.get("ids", [])
                maxTotal = float(g.get("maxTotal") or 0.0)
                subweight = float(g.get("subweight") or 0.0)
                total = 0.0
                # Sum available scores; missing/blank treated as 0
                for aid in ids:
                    v = score_map.get(aid)
                    if v is None:
                        # treat blank as 0
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
                reqpct = round((eq_pct * subweight) / 100.0, 2)
                stud_res[gkey] = {
                    "total": round(total, 2),
                    "eq_pct": round(eq_pct, 2),
                    "reqpct": reqpct,
                    # Provide a display-friendly value for legacy UI where the required display is scaled (e.g. 5.00 instead of 50.00)
                    # reqpct_display divides the percent value by 10 for the requested format (adjust if your display rule differs)
                    "reqpct_display": round(reqpct / 10.0, 2),
                }

            results[str(sid)] = stud_res

        return jsonify({"results": results}), 200
    except Exception as exc:
        # Return generic error but include message for dev debugging
        return jsonify({"error": "failed_to_compute", "message": str(exc)}), 500
