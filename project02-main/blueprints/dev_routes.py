import json
import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash
from utils.db_conn import get_db_connection

logger = logging.getLogger(__name__)


dev_bp = Blueprint("dev", __name__)


@dev_bp.route("/grade-test", endpoint="grade_test")
def grade_test():
    return render_template("grade_test.html")


@dev_bp.route("/test-grade-normalizer/<class_id>", endpoint="test_grade_normalizer")
def test_grade_normalizer(class_id):
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

            cursor.execute(
                """
                SELECT 
                    sc.*, 
                    s.id as student_id,
                    s.course as student_course,
                    s.year_level,
                    s.section as student_section,
                    u.school_id,
                    pi.first_name,
                    pi.last_name,
                    pi.middle_name
                FROM student_classes sc
                JOIN students s ON sc.student_id = s.id
                JOIN users u ON s.user_id = u.id
                LEFT JOIN personal_info pi ON s.personal_info_id = pi.id
                WHERE sc.class_id = %s
                ORDER BY pi.last_name, pi.first_name
                """,
                (class_id,),
            )
            enrollments = cursor.fetchall()

            students = []
            for enrollment in enrollments:
                first_name = enrollment.get("first_name") or ""
                middle_name = enrollment.get("middle_name") or ""
                last_name = enrollment.get("last_name") or ""
                school_id = enrollment.get("school_id") or ""

                if first_name and last_name:
                    student_name = (
                        f"{last_name}, {first_name} {middle_name}".strip()
                        if middle_name
                        else f"{last_name}, {first_name}"
                    )
                else:
                    student_name = (
                        school_id or f"Student {enrollment.get('student_id')}"
                    )

                cursor.execute(
                    """
                    SELECT ss.*, ga.name as assessment_name 
                    FROM student_scores ss
                    JOIN grade_assessments ga ON ss.assessment_id = ga.id
                    WHERE ss.student_id = %s
                    """,
                    (enrollment.get("student_id"),),
                )
                scores = {
                    score["assessment_name"]: score["score"]
                    for score in cursor.fetchall()
                }

                students.append(
                    {
                        "id": enrollment.get("student_id"),
                        "name": student_name,
                        "school_id": school_id,
                        "scores": scores,
                    }
                )

            return render_template(
                "test_grade_normalizer.html",
                structure=structure,
                students=students,
                class_id=class_id,
            )

    except Exception as e:
        import traceback

        logger.error(
            f"Error in test_grade_normalizer: {str(e)}\n{traceback.format_exc()}"
        )
        return f"<pre style='color:red;'>{traceback.format_exc()}</pre>"
