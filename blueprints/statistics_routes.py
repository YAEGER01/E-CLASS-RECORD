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
                WHERE c.instructor_id = %s
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
                    "total_scores": score_row["total_scores"],
                    "avg_score": round(score_row["avg_score"] or 0, 2),
                    "min_score": score_row["min_score"] or 0,
                    "max_score": score_row["max_score"] or 0,
                    "students_with_scores": score_row["students_with_scores"],
                    "total_assessments": score_row["total_assessments"],
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
                    grade_stats["passing_count"] = pass_row["passing_scores"]
                    grade_stats["failing_count"] = (
                        pass_row["total_scores"] - pass_row["passing_scores"]
                    )

            stats = {
                "total_classes": total_classes,
                "total_students": total_students,
                "avg_class_size": round(avg_class_size, 1),
                "classes": classes_data,
                "grade_stats": grade_stats,
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
