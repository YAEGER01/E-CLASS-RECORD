from flask import Blueprint, jsonify, request
from utils.db_conn import get_db_connection
from utils.statistics_utils import get_class_advanced_stats

statistics_bp = Blueprint("statistics", __name__)


@statistics_bp.route("/api/class/<int:class_id>/stats", methods=["GET"])
def class_main_stats(class_id):
    try:
        with get_db_connection().cursor() as cursor:
            # Get total classes for this instructor
            cursor.execute(
                "SELECT instructor_id FROM classes WHERE id = %s", (class_id,)
            )
            row = cursor.fetchone()
            if not row:
                return jsonify({"error": "Class not found"}), 404
            instructor_id = row["instructor_id"]

            cursor.execute(
                "SELECT COUNT(*) as count FROM classes WHERE instructor_id = %s",
                (instructor_id,),
            )
            total_classes = cursor.fetchone()["count"]

            cursor.execute(
                """
                SELECT COUNT(DISTINCT sc.student_id) as count
                FROM student_classes sc
                JOIN classes c ON sc.class_id = c.id
                WHERE c.instructor_id = %s AND sc.status = 'approved'
            """,
                (instructor_id,),
            )
            total_students = cursor.fetchone()["count"]

            avg_class_size = total_students / total_classes if total_classes > 0 else 0

            cursor.execute(
                """
                SELECT c.id, c.class_code, c.subject, c.course, c.section,
                       COUNT(DISTINCT sc.student_id) as student_count,
                       COUNT(DISTINCT ga.id) as assessment_count
                FROM classes c
                LEFT JOIN student_classes sc ON c.id = sc.class_id AND sc.status = 'approved'
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

            # Grade statistics
            grade_stats = {}
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
                    "total_scores": int(score_row["total_scores"] or 0),
                    "avg_score": round(score_row["avg_score"] or 0, 2),
                    "min_score": int(score_row["min_score"] or 0),
                    "max_score": int(score_row["max_score"] or 0),
                    "students_with_scores": int(score_row["students_with_scores"] or 0),
                    "total_assessments": int(score_row["total_assessments"] or 0),
                    "score_range": f"{score_row['min_score'] or 0} - {score_row['max_score'] or 0}",
                }
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
                        (pass_row["passing_scores"] / pass_row["total_scores"]) * 100,
                        1,
                    )
                    grade_stats["passing_count"] = int(pass_row["passing_scores"] or 0)
                    grade_stats["failing_count"] = int(
                        (pass_row["total_scores"] or 0) - (pass_row["passing_scores"] or 0)
                    )

            # Calculate grade distribution (A/B/C/D/F)
            grade_distribution = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
            cursor.execute(
                """
                SELECT
                    SUM(CASE WHEN ss.score >= 90 THEN 1 ELSE 0 END) as grade_a,
                    SUM(CASE WHEN ss.score >= 80 AND ss.score < 90 THEN 1 ELSE 0 END) as grade_b,
                    SUM(CASE WHEN ss.score >= 70 AND ss.score < 80 THEN 1 ELSE 0 END) as grade_c,
                    SUM(CASE WHEN ss.score >= 60 AND ss.score < 70 THEN 1 ELSE 0 END) as grade_d,
                    SUM(CASE WHEN ss.score < 60 THEN 1 ELSE 0 END) as grade_f
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
            dist_row = cursor.fetchone()
            if dist_row:
                grade_distribution = {
                    "A": int(dist_row["grade_a"] or 0),
                    "B": int(dist_row["grade_b"] or 0),
                    "C": int(dist_row["grade_c"] or 0),
                    "D": int(dist_row["grade_d"] or 0),
                    "F": int(dist_row["grade_f"] or 0),
                }

            # Calculate assessment trends (assessment names and average scores)
            assessment_trends = {"labels": [], "scores": []}
            cursor.execute(
                """
                SELECT
                    ga.id,
                    ga.name as assessment_name,
                    AVG(ss.score) as avg_score,
                    ga.max_score,
                    ga.created_at
                FROM grade_assessments ga
                LEFT JOIN student_scores ss ON ga.id = ss.assessment_id
                WHERE ga.subcategory_id IN (
                    SELECT gsc.id FROM grade_subcategories gsc
                    JOIN grade_categories gc ON gsc.category_id = gc.id
                    JOIN grade_structures gs ON gc.structure_id = gs.id
                    WHERE gs.class_id IN (
                        SELECT id FROM classes WHERE instructor_id = %s
                    )
                )
                GROUP BY ga.id, ga.name, ga.max_score, ga.created_at
                ORDER BY ga.created_at ASC
            """,
                (instructor_id,),
            )
            trends = cursor.fetchall()
            if trends:
                # Normalize scores to percentage (0-100)
                trend_labels = []
                trend_scores = []
                for t in trends:
                    avg_score = t["avg_score"] or 0
                    max_score = t["max_score"] or 100
                    # Convert to percentage
                    percentage_score = (avg_score / max_score * 100) if max_score > 0 else 0
                    trend_labels.append(t["assessment_name"])
                    trend_scores.append(round(percentage_score, 2))
                
                assessment_trends = {
                    "labels": trend_labels,
                    "scores": trend_scores,
                }

            # Calculate score distribution by ranges (0-20%, 20-40%, 40-60%, 60-80%, 80-100%)
            score_distribution = {"0-20": 0, "20-40": 0, "40-60": 0, "60-80": 0, "80-100": 0}
            cursor.execute(
                """
                SELECT
                    SUM(CASE WHEN (ss.score / ga.max_score * 100) >= 0 AND (ss.score / ga.max_score * 100) < 20 THEN 1 ELSE 0 END) as range_0_20,
                    SUM(CASE WHEN (ss.score / ga.max_score * 100) >= 20 AND (ss.score / ga.max_score * 100) < 40 THEN 1 ELSE 0 END) as range_20_40,
                    SUM(CASE WHEN (ss.score / ga.max_score * 100) >= 40 AND (ss.score / ga.max_score * 100) < 60 THEN 1 ELSE 0 END) as range_40_60,
                    SUM(CASE WHEN (ss.score / ga.max_score * 100) >= 60 AND (ss.score / ga.max_score * 100) < 80 THEN 1 ELSE 0 END) as range_60_80,
                    SUM(CASE WHEN (ss.score / ga.max_score * 100) >= 80 THEN 1 ELSE 0 END) as range_80_100
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
            dist_row = cursor.fetchone()
            if dist_row:
                score_distribution = {
                    "0-20": int(dist_row["range_0_20"] or 0),
                    "20-40": int(dist_row["range_20_40"] or 0),
                    "40-60": int(dist_row["range_40_60"] or 0),
                    "60-80": int(dist_row["range_60_80"] or 0),
                    "80-100": int(dist_row["range_80_100"] or 0),
                }

            stats = {
                "total_classes": total_classes,
                "total_students": total_students,
                "avg_class_size": round(avg_class_size, 1),
                "classes": classes_data,
                "grade_stats": grade_stats,
                "grade_distribution": grade_distribution,
                "assessment_trends": assessment_trends,
                "score_distribution": score_distribution,
            }
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@statistics_bp.route("/api/class/<int:class_id>/advanced-stats", methods=["GET"])
def class_advanced_stats(class_id):
    try:
        stats = get_class_advanced_stats(class_id)
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@statistics_bp.route("/api/class/<int:class_id>/performance-trends", methods=["GET"])
def class_performance_trends(class_id):
    try:
        from utils.statistics_utils import calculate_performance_trends

        stats = calculate_performance_trends(class_id)
        if stats is None:
            return (
                jsonify({"error": "Insufficient data for performance trends analysis"}),
                400,
            )
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@statistics_bp.route("/api/class/<int:class_id>/difficulty-analysis", methods=["GET"])
def class_difficulty_analysis(class_id):
    try:
        from utils.statistics_utils import calculate_assessment_difficulty_analysis

        stats = calculate_assessment_difficulty_analysis(class_id)
        if stats is None:
            return jsonify({"error": "Insufficient data for difficulty analysis"}), 400
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@statistics_bp.route("/api/class/<int:class_id>/progress-analysis", methods=["GET"])
def class_progress_analysis(class_id):
    try:
        from utils.statistics_utils import calculate_learning_progress_analysis

        stats = calculate_learning_progress_analysis(class_id)
        if stats is None:
            return jsonify({"error": "Insufficient data for progress analysis"}), 400
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@statistics_bp.route(
    "/api/class/<int:class_id>/comprehensive-analytics", methods=["GET"]
)
def class_comprehensive_analytics(class_id):
    try:
        from utils.statistics_utils import get_comprehensive_class_analytics

        stats = get_comprehensive_class_analytics(class_id)
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@statistics_bp.route("/api/class/<int:class_id>/correlation-analysis", methods=["GET"])
def class_correlation_analysis(class_id):
    try:
        from utils.statistics_utils import calculate_correlation_analysis

        stats = calculate_correlation_analysis(class_id)
        if stats is None:
            return jsonify({"error": "Insufficient data for correlation analysis"}), 400
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@statistics_bp.route("/api/class/<int:class_id>/grade-distribution", methods=["GET"])
def class_grade_distribution(class_id):
    try:
        from utils.statistics_utils import calculate_grade_distribution_analysis

        stats = calculate_grade_distribution_analysis(class_id)
        if stats is None:
            return (
                jsonify({"error": "Insufficient data for grade distribution analysis"}),
                400,
            )
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@statistics_bp.route("/api/class/<int:class_id>/risk-analysis", methods=["GET"])
def class_risk_analysis(class_id):
    try:
        from utils.statistics_utils import calculate_risk_analysis

        stats = calculate_risk_analysis(class_id)
        if stats is None:
            return jsonify({"error": "Insufficient data for risk analysis"}), 400
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@statistics_bp.route("/api/class/<int:class_id>/full-analytics", methods=["GET"])
def class_full_analytics(class_id):
    try:
        from utils.statistics_utils import get_comprehensive_class_analytics_v2

        stats = get_comprehensive_class_analytics_v2(class_id)
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
