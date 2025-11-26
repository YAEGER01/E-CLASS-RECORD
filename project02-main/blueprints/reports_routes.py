import logging
import os
from datetime import datetime
from flask import Blueprint, jsonify, request, session, send_file
from flask_mail import Message
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from utils.auth_utils import login_required
from utils.db_conn import get_db_connection

logger = logging.getLogger(__name__)

reports_bp = Blueprint("reports", __name__)


def _require_instructor():
    """Helper to check if current user is an instructor and return their ID."""
    if session.get("role") != "instructor":
        return jsonify({"error": "Access denied. Instructor privileges required."}), 403

    try:
        with get_db_connection().cursor() as cursor:
            cursor.execute(
                "SELECT id FROM instructors WHERE user_id = %s", (session["user_id"],)
            )
            instructor = cursor.fetchone()
            if not instructor:
                return jsonify({"error": "Instructor profile not found"}), 404
            return instructor["id"]
    except Exception as e:
        logger.error(f"Error getting instructor ID: {str(e)}")
        return jsonify({"error": "Database error"}), 500


def _require_student():
    """Helper to check if current user is a student and return their ID."""
    if session.get("role") != "student":
        return jsonify({"error": "Access denied. Student privileges required."}), 403

    try:
        with get_db_connection().cursor() as cursor:
            cursor.execute(
                "SELECT id FROM students WHERE user_id = %s", (session["user_id"],)
            )
            student = cursor.fetchone()
            if not student:
                return jsonify({"error": "Student profile not found"}), 404
            return student["id"]
    except Exception as e:
        logger.error(f"Error getting student ID: {str(e)}")
        return jsonify({"error": "Database error"}), 500


@reports_bp.route("/api/send-grade-notification", methods=["POST"])
@login_required
def send_grade_notification():
    """Send email notification about grade release to students."""
    from app import mail  # Import here to avoid circular import

    instructor_id = _require_instructor()
    if not isinstance(instructor_id, int):
        return instructor_id  # Error response

    try:
        data = request.get_json() or {}
        class_id = data.get("class_id")
        student_ids = data.get("student_ids", [])
        message = data.get("message", "")

        if not class_id:
            return jsonify({"error": "class_id is required"}), 400

        with get_db_connection().cursor() as cursor:
            # Get class details
            cursor.execute(
                "SELECT course, subject, class_code FROM classes WHERE id = %s AND instructor_id = %s",
                (class_id, instructor_id),
            )
            class_info = cursor.fetchone()
            if not class_info:
                return jsonify({"error": "Class not found or access denied"}), 404

            # Get student emails
            if student_ids:
                # Specific students
                placeholders = ",".join(["%s"] * len(student_ids))
                cursor.execute(
                    f"""
                    SELECT s.id, u.email, pi.first_name, pi.last_name
                    FROM students s
                    JOIN users u ON s.user_id = u.id
                    LEFT JOIN personal_info pi ON s.personal_info_id = pi.id
                    WHERE s.id IN ({placeholders}) AND s.id IN (
                        SELECT sc.student_id FROM student_classes sc WHERE sc.class_id = %s
                    )
                    """,
                    student_ids + [class_id],
                )
            else:
                # All students in class
                cursor.execute(
                    """
                    SELECT s.id, u.email, pi.first_name, pi.last_name
                    FROM students s
                    JOIN users u ON s.user_id = u.id
                    LEFT JOIN personal_info pi ON s.personal_info_id = pi.id
                    JOIN student_classes sc ON s.id = sc.student_id
                    WHERE sc.class_id = %s
                    """,
                    (class_id,),
                )

            students = cursor.fetchall()

            sent_count = 0
            failed_count = 0

            for student in students:
                if not student.get("email"):
                    failed_count += 1
                    continue

                try:
                    student_name = (
                        f"{student.get('first_name', '')} {student.get('last_name', '')}".strip()
                        or "Student"
                    )

                    msg = Message(
                        subject=f"Grade Release Notification - {class_info['course']}",
                        recipients=[student["email"]],
                        body=f"""Dear {student_name},

{class_info['subject']} ({class_info['course']}) - {class_info['class_code']}

{message}

Your grades have been released. Please log in to the E-Class Record system to view your grades.

Best regards,
Your Instructor
""",
                    )

                    mail.send(msg)
                    sent_count += 1

                except Exception as e:
                    logger.error(
                        f"Failed to send email to {student['email']}: {str(e)}"
                    )
                    failed_count += 1

            return jsonify(
                {
                    "message": f"Notifications sent: {sent_count}, Failed: {failed_count}",
                    "sent": sent_count,
                    "failed": failed_count,
                }
            )

    except Exception as e:
        logger.error(f"Error sending grade notifications: {str(e)}")
        return jsonify({"error": "Failed to send notifications"}), 500


@reports_bp.route("/api/export/class-grades/<int:class_id>", methods=["GET"])
@login_required
def export_class_grades_pdf(class_id):
    """Export class grades as PDF report."""
    instructor_id = _require_instructor()
    if not isinstance(instructor_id, int):
        return instructor_id  # Error response

    try:
        with get_db_connection().cursor() as cursor:
            # Verify instructor owns this class
            cursor.execute(
                "SELECT course, subject, class_code, section FROM classes WHERE id = %s AND instructor_id = %s",
                (class_id, instructor_id),
            )
            class_info = cursor.fetchone()
            if not class_info:
                return jsonify({"error": "Class not found or access denied"}), 404

            # Get computed grades using the calculate API
            from blueprints.instructor_routes import api_calculate_class_grades

            response = api_calculate_class_grades(class_id)
            if hasattr(response, "get_json"):
                grades_data = response.get_json()
            else:
                return jsonify({"error": "Failed to compute grades"}), 500

            if "computed_grades" not in grades_data:
                return jsonify({"error": "No computed grades available"}), 404

            computed_grades = grades_data["computed_grades"]

            # Get student names
            student_ids = [g["student_id"] for g in computed_grades]
            if student_ids:
                placeholders = ",".join(["%s"] * len(student_ids))
                cursor.execute(
                    f"""
                    SELECT s.id, pi.first_name, pi.last_name
                    FROM students s
                    LEFT JOIN personal_info pi ON s.personal_info_id = pi.id
                    WHERE s.id IN ({placeholders})
                    """,
                    student_ids,
                )
                student_names = {
                    row[
                        "id"
                    ]: f"{row.get('first_name', '')} {row.get('last_name', '')}".strip()
                    or f"Student {row['id']}"
                    for row in cursor.fetchall()
                }
            else:
                student_names = {}

            # Generate PDF
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = []

            # Title
            title = Paragraph(f"Grade Report - {class_info['course']}", styles["Title"])
            elements.append(title)
            elements.append(Spacer(1, 12))

            # Class info
            class_info_text = f"""
            Subject: {class_info['subject']}<br/>
            Course: {class_info['course']}<br/>
            Section: {class_info['section']}<br/>
            Class Code: {class_info['class_code']}<br/>
            Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            elements.append(Paragraph(class_info_text, styles["Normal"]))
            elements.append(Spacer(1, 20))

            # Grades table
            data = [["Student ID", "Student Name", "Final Grade", "Equivalent"]]

            for grade in sorted(computed_grades, key=lambda x: x["student_id"]):
                student_name = student_names.get(
                    grade["student_id"], f"Student {grade['student_id']}"
                )
                data.append(
                    [
                        str(grade["student_id"]),
                        student_name,
                        f"{grade['final_grade']:.2f}%",
                        grade["equivalent"],
                    ]
                )

            table = Table(data)
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 14),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ]
                )
            )

            elements.append(table)

            # Summary statistics
            elements.append(Spacer(1, 20))
            elements.append(Paragraph("Summary Statistics:", styles["Heading2"]))

            if computed_grades:
                grades = [g["final_grade"] for g in computed_grades]
                avg_grade = sum(grades) / len(grades)
                min_grade = min(grades)
                max_grade = max(grades)

                passing_count = sum(1 for g in grades if g >= 60)
                pass_rate = (passing_count / len(grades)) * 100

                stats_text = f"""
                Total Students: {len(computed_grades)}<br/>
                Average Grade: {avg_grade:.2f}%<br/>
                Highest Grade: {max_grade:.2f}%<br/>
                Lowest Grade: {min_grade:.2f}%<br/>
                Pass Rate (≥60%): {pass_rate:.1f}%
                """
                elements.append(Paragraph(stats_text, styles["Normal"]))

            doc.build(elements)

            buffer.seek(0)
            filename = f"grade_report_{class_info['class_code']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

            return send_file(
                buffer,
                as_attachment=True,
                download_name=filename,
                mimetype="application/pdf",
            )

    except Exception as e:
        logger.error(f"Error generating PDF report: {str(e)}")
        return jsonify({"error": "Failed to generate report"}), 500


@reports_bp.route("/api/export/student-grades", methods=["GET"])
@login_required
def export_student_grades_pdf():
    """Export student's own grades as PDF report."""
    student_id = _require_student()
    if not isinstance(student_id, int):
        return student_id  # Error response

    try:
        with get_db_connection().cursor() as cursor:
            # Get student info
            cursor.execute(
                """
                SELECT s.id, pi.first_name, pi.last_name, pi.middle_name
                FROM students s
                LEFT JOIN personal_info pi ON s.personal_info_id = pi.id
                WHERE s.id = %s
                """,
                (student_id,),
            )
            student_info = cursor.fetchone()
            if not student_info:
                return jsonify({"error": "Student profile not found"}), 404

            student_name = (
                f"{student_info.get('first_name', '')} {student_info.get('last_name', '')}".strip()
                or f"Student {student_id}"
            )

            # Get all classes and grades for this student
            cursor.execute(
                """
                SELECT c.id, c.class_code, c.course, c.subject, c.section
                FROM classes c
                JOIN student_classes sc ON c.id = sc.class_id
                WHERE sc.student_id = %s
                ORDER BY c.created_at DESC
                """,
                (student_id,),
            )
            classes = cursor.fetchall()

            # Generate PDF
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = []

            # Title
            title = Paragraph(f"Student Grade Report - {student_name}", styles["Title"])
            elements.append(title)
            elements.append(Spacer(1, 12))

            # Student info
            student_info_text = f"""
            Student ID: {student_id}<br/>
            Name: {student_name}<br/>
            Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            elements.append(Paragraph(student_info_text, styles["Normal"]))
            elements.append(Spacer(1, 20))

            total_classes = 0
            total_grades = []

            for class_info in classes:
                class_id = class_info["id"]

                # Try to get computed grade for this class
                try:
                    from blueprints.student_routes import get_student_class_grades

                    # This is a route function, we need to simulate the request
                    # For now, let's get from snapshots
                    cursor.execute(
                        """
                        SELECT gs.grade_payload, gs.created_at
                        FROM grade_snapshots gs
                        WHERE gs.class_id = %s AND JSON_CONTAINS(
                            JSON_EXTRACT(gs.snapshot_json, '$.students[*].student_id'),
                            %s
                        )
                        ORDER BY gs.id DESC LIMIT 1
                        """,
                        (class_id, student_id),
                    )
                    snapshot = cursor.fetchone()

                    if snapshot and snapshot["grade_payload"]:
                        import json

                        grade_data = json.loads(snapshot["grade_payload"])
                        final_grade = grade_data.get("final_grade")
                        equivalent = grade_data.get("equivalent")

                        if final_grade is not None:
                            total_classes += 1
                            total_grades.append(final_grade)

                            # Add class entry
                            class_title = Paragraph(
                                f"{class_info['course']} - {class_info['subject']}",
                                styles["Heading3"],
                            )
                            elements.append(class_title)

                            grade_text = f"""
                            Class Code: {class_info['class_code']}<br/>
                            Section: {class_info['section']}<br/>
                            Final Grade: {final_grade:.2f}%<br/>
                            Equivalent: {equivalent}<br/>
                            Released: {snapshot['created_at'].strftime('%Y-%m-%d %H:%M:%S')}
                            """
                            elements.append(Paragraph(grade_text, styles["Normal"]))
                            elements.append(Spacer(1, 12))

                except Exception as e:
                    logger.warning(
                        f"Could not get grade for class {class_id}: {str(e)}"
                    )
                    continue

            # Summary
            if total_grades:
                avg_grade = sum(total_grades) / len(total_grades)
                summary_text = f"""
                <b>Summary:</b><br/>
                Total Classes: {total_classes}<br/>
                Average Grade: {avg_grade:.2f}%<br/>
                GPA Equivalent: {_calculate_gpa_equivalent(avg_grade)}
                """
                elements.append(Paragraph(summary_text, styles["Normal"]))

            doc.build(elements)

            buffer.seek(0)
            filename = f"student_report_{student_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

            return send_file(
                buffer,
                as_attachment=True,
                download_name=filename,
                mimetype="application/pdf",
            )

    except Exception as e:
        logger.error(f"Error generating student PDF report: {str(e)}")
        return jsonify({"error": "Failed to generate report"}), 500


def _calculate_gpa_equivalent(avg_grade):
    """Convert average grade to GPA equivalent."""
    if avg_grade >= 96:
        return "1.00"
    elif avg_grade >= 93:
        return "1.25"
    elif avg_grade >= 90:
        return "1.50"
    elif avg_grade >= 87:
        return "1.75"
    elif avg_grade >= 84:
        return "2.00"
    elif avg_grade >= 81:
        return "2.25"
    elif avg_grade >= 78:
        return "2.50"
    elif avg_grade >= 75:
        return "2.75"
    else:
        return "5.00"
