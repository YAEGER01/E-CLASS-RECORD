from flask import request
from utils.db_conn import get_db_connection


def get_equivalent(final_grade: float) -> str:
    """Map numeric grade to equivalent string. Keep in sync with app.py or centralize later."""
    if final_grade >= 96:
        return "1.00"
    if final_grade >= 93:
        return "1.25"
    if final_grade >= 90:
        return "1.50"
    if final_grade >= 87:
        return "1.75"
    if final_grade >= 84:
        return "2.00"
    if final_grade >= 81:
        return "2.25"
    if final_grade >= 78:
        return "2.50"
    if final_grade >= 75:
        return "2.75"
    return "5.00"


def perform_grade_computation(
    formula: dict, normalized_rows: list, student_scores_named: list[dict]
) -> list[dict]:
    """Compute per-student grades.

    Assumptions:
    - normalized_rows contain repeated 'weight' per group name; we sum unique group weights per (category, name)
    - If formula defines category parts with weights, we use the sum of those weights as the category's total weight.
      We scale the category contribution from structure weights to match the formula total weight. If structure weight is 0,
      we use category average percent * formula total weight.
    - student_scores_named carries {'student_id', 'assessment_name', 'score'}; we match by assessment_name to normalized rows.
    """
    # Build lookup: assessment_name -> (category, group_name, max_score, group_weight)
    assess_lookup = {}
    # Also compute per-category group weights and assessment sets
    from collections import defaultdict

    category_group_weights = defaultdict(float)  # (category, group_name) -> weight
    category_assessments = defaultdict(list)  # category -> list of assessment names

    for row in normalized_rows:
        aname = row.get("assessment")
        category = row.get("category")
        gname = row.get("name")
        weight = float(row.get("weight") or 0)
        max_score = float(row.get("max_score") or 0)
        if aname:
            assess_lookup[aname] = (category, gname, max_score, weight)
            if category:
                category_assessments[category].append(aname)
        if category and gname:
            # Sum unique group weight: last one wins if repeated; we'll just ensure it's set (weights should be same per group's assessments)
            category_group_weights[(category, gname)] = weight

    # Compute category total weight from structure
    category_weight_structure = defaultdict(float)
    for (category, gname), w in category_group_weights.items():
        category_weight_structure[category] += float(w or 0)

    # Compute category total weight from formula (sum of parts)
    category_weight_formula = {}
    if isinstance(formula, dict):
        for category, details in formula.items():
            if isinstance(details, dict):
                total_w = 0.0
                for part in details.values():
                    try:
                        total_w += float(part.get("weight", 0))
                    except Exception:
                        continue
                category_weight_formula[category] = total_w

    # Group scores per student
    by_student = defaultdict(list)
    for rec in student_scores_named:
        sid = rec.get("student_id")
        aname = rec.get("assessment_name")
        score = rec.get("score")
        if sid is None or aname is None:
            continue
        by_student[sid].append((aname, float(score or 0)))

    results = []
    for student_id, pairs in by_student.items():
        # category -> { group_name -> (sum_score, sum_max) }
        cat_group_totals = defaultdict(lambda: defaultdict(lambda: [0.0, 0.0]))
        for aname, score in pairs:
            if aname not in assess_lookup:
                # Unknown assessment (not in current structure); skip
                continue
            category, gname, max_score, gweight = assess_lookup[aname]
            if max_score and max_score > 0:
                cat_group_totals[category][gname][0] += float(score)
                cat_group_totals[category][gname][1] += float(max_score)

        total_grade = 0.0
        for category, groups in cat_group_totals.items():
            # Compute contribution by groups using structure group weights
            cat_contrib = 0.0
            for gname, (sum_score, sum_max) in groups.items():
                if sum_max <= 0:
                    continue
                avg_percent = sum_score / sum_max  # 0..1
                gweight = category_group_weights.get((category, gname), 0.0)
                cat_contrib += avg_percent * gweight

            # Scale category contribution if formula dictates a different total weight
            desired_w = category_weight_formula.get(category)
            struct_w = category_weight_structure.get(category) or 0.0
            if desired_w is not None:
                if struct_w > 0:
                    cat_contrib = cat_contrib * (desired_w / struct_w)
                else:
                    # No structure weights; fallback to averaging all assessments in the category
                    assessments = category_assessments.get(category, [])
                    if assessments:
                        sum_score = 0.0
                        sum_max = 0.0
                        for aname in assessments:
                            # find student's score for this assessment
                            for a2, sc2 in pairs:
                                if a2 == aname:
                                    _, _, mx, _ = assess_lookup.get(
                                        a2, (None, None, 0.0, 0.0)
                                    )
                                    sum_score += sc2
                                    sum_max += float(mx or 0)
                        if sum_max > 0:
                            cat_contrib = (sum_score / sum_max) * desired_w

            total_grade += cat_contrib

        final_grade = round(total_grade, 2)
        equivalent = get_equivalent(final_grade)
        results.append(
            {
                "student_id": student_id,
                "final_grade": final_grade,
                "equivalent": equivalent,
            }
        )

    # Include students with no scores yet (enrolled but missing in by_student)
    try:
        with get_db_connection().cursor() as cursor:
            cursor.execute(
                "SELECT sc.student_id FROM student_classes sc WHERE sc.class_id = %s",
                (
                    (
                        request.view_args.get("class_id")
                        if request and getattr(request, "view_args", None)
                        else None
                    ),
                ),
            )
            enrolled = [row["student_id"] for row in cursor.fetchall() or []]
    except Exception:
        enrolled = []
    existing_ids = {r["student_id"] for r in results}
    for sid in enrolled:
        if sid not in existing_ids:
            results.append(
                {"student_id": sid, "final_grade": 0.0, "equivalent": "5.00"}
            )

    return sorted(results, key=lambda r: r["student_id"])  # stable order
