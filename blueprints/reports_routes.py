from flask import Blueprint, jsonify, render_template, request
from utils.auth_utils import login_required
from utils.db_conn import get_db_connection
from datetime import datetime
import json

reports_bp = Blueprint("reports", __name__)


def abbreviate_assessment(name):
    """Convert assessment name to abbreviation for remarks."""
    name_upper = name.upper()
    if "PRELIM" in name_upper and "EXAM" in name_upper:
        return "NPE"
    elif "MIDTERM" in name_upper and "EXAM" in name_upper:
        return "NME"
    elif "FINAL" in name_upper and "EXAM" in name_upper:
        return "NFE"
    elif "PROJECT" in name_upper:
        return "NO PROJECT"
    else:
        return f"NO {name_upper}"


@reports_bp.route("/api/reports/grade-sheet/<int:class_id>", methods=["GET"])
@login_required
def generate_grade_sheet_report(class_id):
    """Generate a comprehensive HTML grade sheet report for a class"""
    # Store class_id early to avoid scope issues
    current_class_id = class_id

    try:
        with get_db_connection().cursor() as cursor:
            # Get class information
            cursor.execute(
                """
                SELECT class_code, course, subject, section, schedule, class_type, instructor_id,
                       year, semester, track, subject_code, units
                FROM classes
                WHERE id = %s
            """,
                (class_id,),
            )
            class_row = cursor.fetchone()

            if not class_row:
                return jsonify({"error": "Class not found"}), 404

            # Extract values for both tuple and dict responses
            course = (
                class_row[1]
                if isinstance(class_row, tuple)
                else class_row.get("course")
            )
            subject = (
                class_row[2]
                if isinstance(class_row, tuple)
                else class_row.get("subject")
            )
            section = (
                class_row[3]
                if isinstance(class_row, tuple)
                else class_row.get("section")
            )
            year = (
                class_row[7] if isinstance(class_row, tuple) else class_row.get("year")
            )
            semester = (
                class_row[8]
                if isinstance(class_row, tuple)
                else class_row.get("semester")
            )
            track = (
                class_row[9] if isinstance(class_row, tuple) else class_row.get("track")
            )
            subject_code = (
                class_row[10]
                if isinstance(class_row, tuple)
                else class_row.get("subject_code")
            )
            units = (
                class_row[11]
                if isinstance(class_row, tuple)
                else class_row.get("units")
            )

            # Build standardized class_id
            year_str = str(year) if year else ""
            formatted_year = year_str[-2:] if len(year_str) >= 2 else year_str

            semester_str = str(semester) if semester else ""
            formatted_semester = (
                "1"
                if "1st" in semester_str
                else "2" if "2nd" in semester_str else semester_str
            )

            computed_class_id = f"{formatted_year}-{formatted_semester} {course} {section}-{track} ({subject_code} - {subject})"
            class_section = f"{course or ''} {section or ''}-{track or ''}".strip()

            class_info = {
                "class_code": (
                    class_row[0]
                    if isinstance(class_row, tuple)
                    else class_row.get("class_code")
                ),
                "course": course,
                "subject": subject,
                "subject_code": subject_code,
                "units": units,
                "section": section,
                "schedule": (
                    class_row[4]
                    if isinstance(class_row, tuple)
                    else class_row.get("schedule")
                ),
                "class_type": (
                    class_row[5]
                    if isinstance(class_row, tuple)
                    else class_row.get("class_type")
                ),
                "class_id": computed_class_id,
                "class_section": class_section,
                "instructor_name": "INSTRUCTOR",
            }

            # Get instructor name
            instructor_id = (
                class_row[6]
                if isinstance(class_row, tuple)
                else class_row.get("instructor_id")
            )
            cursor.execute(
                """
                SELECT pi.first_name, pi.last_name
                FROM instructors i
                LEFT JOIN personal_info pi ON i.personal_info_id = pi.id
                WHERE i.id = %s
            """,
                (instructor_id,),
            )
            instructor_row = cursor.fetchone()
            if instructor_row:
                inst_first = (
                    instructor_row[0]
                    if isinstance(instructor_row, tuple)
                    else instructor_row.get("first_name")
                )
                inst_last = (
                    instructor_row[1]
                    if isinstance(instructor_row, tuple)
                    else instructor_row.get("last_name")
                )
                class_info["instructor_name"] = (
                    f"{inst_first} {inst_last}".strip().upper()
                    if inst_first and inst_last
                    else "INSTRUCTOR"
                )

            # Get signature data (if exists)
            cursor.execute(
                """
                SELECT submitted_by_name, submitted_by_title,
                       checked_by_name, checked_by_title,
                       countersigned_by_name, countersigned_by_title,
                       noted_by_name, noted_by_title
                FROM grade_sheet_signatures
                WHERE class_id = %s
            """,
                (class_id,),
            )
            sig_row = cursor.fetchone()

            if sig_row:
                signatures = {
                    "submitted_by_name": (
                        sig_row[0]
                        if isinstance(sig_row, tuple)
                        else sig_row.get("submitted_by_name")
                        or class_info["instructor_name"]
                    ),
                    "submitted_by_title": (
                        sig_row[1]
                        if isinstance(sig_row, tuple)
                        else sig_row.get("submitted_by_title")
                        or "Assistant Professor IV"
                    ),
                    "checked_by_name": (
                        sig_row[2]
                        if isinstance(sig_row, tuple)
                        else sig_row.get("checked_by_name") or ""
                    ),
                    "checked_by_title": (
                        sig_row[3]
                        if isinstance(sig_row, tuple)
                        else sig_row.get("checked_by_title") or "Chair, BSIT"
                    ),
                    "countersigned_by_name": (
                        sig_row[4]
                        if isinstance(sig_row, tuple)
                        else sig_row.get("countersigned_by_name") or ""
                    ),
                    "countersigned_by_title": (
                        sig_row[5]
                        if isinstance(sig_row, tuple)
                        else sig_row.get("countersigned_by_title")
                        or "College Secretary"
                    ),
                    "noted_by_name": (
                        sig_row[6]
                        if isinstance(sig_row, tuple)
                        else sig_row.get("noted_by_name") or ""
                    ),
                    "noted_by_title": (
                        sig_row[7]
                        if isinstance(sig_row, tuple)
                        else sig_row.get("noted_by_title") or "Dean, CCSICT"
                    ),
                }
            else:
                # Default signatures if none exist
                signatures = {
                    "submitted_by_name": class_info["instructor_name"],
                    "submitted_by_title": "Assistant Professor IV",
                    "checked_by_name": "",
                    "checked_by_title": "Chair, BSIT",
                    "countersigned_by_name": "",
                    "countersigned_by_title": "College Secretary",
                    "noted_by_name": "",
                    "noted_by_title": "Dean, CCSICT",
                }

            # Get students with their grades from released_grades table
            cursor.execute(
                """
                SELECT s.id, pi.last_name, pi.first_name, pi.middle_name,
                       rg.final_grade, rg.equivalent, u.school_id, rg.remarks
                FROM students s
                JOIN student_classes sc ON s.id = sc.student_id
                JOIN users u ON s.user_id = u.id
                LEFT JOIN personal_info pi ON s.personal_info_id = pi.id
                LEFT JOIN released_grades rg ON s.id = rg.student_id AND rg.class_id = %s
                WHERE sc.class_id = %s AND sc.status = 'approved'
                ORDER BY pi.last_name, pi.first_name
            """,
                (class_id, class_id),
            )
            student_rows = cursor.fetchall()

        # Build students list with computed remarks
        students = []
        passed_count = 0
        failed_count = 0
        incomplete_count = 0

        for row in student_rows:
            if isinstance(row, tuple):
                (
                    student_id,
                    last_name,
                    first_name,
                    middle_name,
                    final_grade,
                    equivalent,
                    school_id,
                    remarks,
                ) = row
            else:
                student_id = row.get("id")
                last_name = row.get("last_name")
                first_name = row.get("first_name")
                middle_name = row.get("middle_name")
                final_grade = row.get("final_grade")
                equivalent = row.get("equivalent")
                school_id = row.get("school_id")
                remarks = row.get("remarks")

            middle_name = middle_name or ""
            # Format name with proper capitalization (Title Case)
            last_name_formatted = last_name.title() if last_name else ""
            first_name_formatted = first_name.title() if first_name else ""
            middle_name_formatted = middle_name.title() if middle_name else ""
            student_name = f"{last_name_formatted}, {first_name_formatted} {middle_name_formatted}".strip()

            # Use remarks from database or calculate if missing
            if not remarks:
                remarks = ""
                if equivalent == "INC":
                    remarks = "INCOMPLETE"
                    incomplete_count += 1
                elif equivalent == "DRP":
                    remarks = "DROPPED"
                elif final_grade:
                    if final_grade >= 75:
                        remarks = "PASSED"
                        passed_count += 1
                    else:
                        remarks = "FAILED"
                        failed_count += 1
            else:
                # Count based on remarks from database
                if (
                    equivalent == "INC"
                    or "NPE" in remarks
                    or "NME" in remarks
                    or "NFE" in remarks
                    or "NO PROJECT" in remarks
                ):
                    incomplete_count += 1
                elif remarks == "PASSED":
                    passed_count += 1
                elif remarks == "FAILED":
                    failed_count += 1

            students.append(
                {
                    "id": student_id,
                    "school_id": school_id,
                    "name": student_name,
                    "final_grade": f"{final_grade:.2f}" if final_grade else "",
                    "equivalent": equivalent if equivalent else "",
                    "remarks": remarks,
                }
            )

        summary = {
            "total": len(students),
            "passed": passed_count,
            "failed": failed_count,
            "incomplete": incomplete_count,
        }

        # Get current date and format period
        current_date = datetime.now().strftime("%B %d, %Y")

        # Build period string from semester and year
        semester_text = semester.upper() if semester else "SEMESTER"
        period = f"{semester_text}, {year}"

        return render_template(
            "grade_sheet_report.html",
            class_id=current_class_id,
            class_info=class_info,
            students=students,
            summary=summary,
            signatures=signatures,
            current_date=current_date,
            period=period,
        )

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@reports_bp.route(
    "/api/reports/grade-sheet/<int:class_id>/signatures", methods=["GET", "POST"]
)
@login_required
def manage_grade_sheet_signatures(class_id):
    """Get or update grade sheet signatures for a class"""
    # Use the shared database connection instead of creating a new one
    conn = get_db_connection()

    try:
        cursor = conn.cursor()

        # Verify class exists and user has permission
        cursor.execute(
            """
            SELECT instructor_id FROM classes WHERE id = %s
        """,
            (class_id,),
        )
        class_row = cursor.fetchone()

        if not class_row:
            cursor.close()
            return jsonify({"error": "Class not found"}), 404

        if request.method == "GET":
            # Get existing signatures
            cursor.execute(
                """
                    SELECT submitted_by_name, submitted_by_title,
                           checked_by_name, checked_by_title,
                           countersigned_by_name, countersigned_by_title,
                           noted_by_name, noted_by_title
                    FROM grade_sheet_signatures
                    WHERE class_id = %s
                """,
                (class_id,),
            )
            sig_row = cursor.fetchone()

            if sig_row:
                signatures = {
                    "submitted_by_name": (
                        sig_row[0]
                        if isinstance(sig_row, tuple)
                        else sig_row.get("submitted_by_name")
                    ),
                    "submitted_by_title": (
                        sig_row[1]
                        if isinstance(sig_row, tuple)
                        else sig_row.get("submitted_by_title")
                    ),
                    "checked_by_name": (
                        sig_row[2]
                        if isinstance(sig_row, tuple)
                        else sig_row.get("checked_by_name")
                    ),
                    "checked_by_title": (
                        sig_row[3]
                        if isinstance(sig_row, tuple)
                        else sig_row.get("checked_by_title")
                    ),
                    "countersigned_by_name": (
                        sig_row[4]
                        if isinstance(sig_row, tuple)
                        else sig_row.get("countersigned_by_name")
                    ),
                    "countersigned_by_title": (
                        sig_row[5]
                        if isinstance(sig_row, tuple)
                        else sig_row.get("countersigned_by_title")
                    ),
                    "noted_by_name": (
                        sig_row[6]
                        if isinstance(sig_row, tuple)
                        else sig_row.get("noted_by_name")
                    ),
                    "noted_by_title": (
                        sig_row[7]
                        if isinstance(sig_row, tuple)
                        else sig_row.get("noted_by_title")
                    ),
                }
            else:
                # Get instructor name for default
                instructor_id = (
                    class_row[0]
                    if isinstance(class_row, tuple)
                    else class_row.get("instructor_id")
                )
                cursor.execute(
                    """
                        SELECT pi.first_name, pi.last_name
                        FROM instructors i
                        LEFT JOIN personal_info pi ON i.personal_info_id = pi.id
                        WHERE i.id = %s
                    """,
                    (instructor_id,),
                )
                instructor_row = cursor.fetchone()

                instructor_name = ""
                if instructor_row:
                    inst_first = (
                        instructor_row[0]
                        if isinstance(instructor_row, tuple)
                        else instructor_row.get("first_name")
                    )
                    inst_last = (
                        instructor_row[1]
                        if isinstance(instructor_row, tuple)
                        else instructor_row.get("last_name")
                    )
                    instructor_name = (
                        f"{inst_first} {inst_last}".strip().upper()
                        if inst_first and inst_last
                        else ""
                    )

                signatures = {
                    "submitted_by_name": instructor_name,
                    "submitted_by_title": "Assistant Professor IV",
                    "checked_by_name": "",
                    "checked_by_title": "Chair, BSIT",
                    "countersigned_by_name": "",
                    "countersigned_by_title": "College Secretary",
                    "noted_by_name": "",
                    "noted_by_title": "Dean, CCSICT",
                }

            return jsonify(signatures), 200

        elif request.method == "POST":
            # Update signatures
            data = request.get_json()
            print(f"[SIGNATURE UPDATE] Received data: {data}")
            print(f"[SIGNATURE UPDATE] Class ID: {class_id}")

            # Check if signature already exists
            cursor.execute(
                """
                SELECT id FROM grade_sheet_signatures WHERE class_id = %s
            """,
                (class_id,),
            )
            existing = cursor.fetchone()
            print(f"[SIGNATURE UPDATE] Existing record: {existing}")

            if existing:
                # Update existing
                print(f"[SIGNATURE UPDATE] Updating existing record")
                cursor.execute(
                    """
                    UPDATE grade_sheet_signatures
                    SET submitted_by_name = %s, submitted_by_title = %s,
                        checked_by_name = %s, checked_by_title = %s,
                        countersigned_by_name = %s, countersigned_by_title = %s,
                        noted_by_name = %s, noted_by_title = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE class_id = %s
                """,
                    (
                        data.get("submitted_by_name"),
                        data.get("submitted_by_title"),
                        data.get("checked_by_name"),
                        data.get("checked_by_title"),
                        data.get("countersigned_by_name"),
                        data.get("countersigned_by_title"),
                        data.get("noted_by_name"),
                        data.get("noted_by_title"),
                        class_id,
                    ),
                )
                print(f"[SIGNATURE UPDATE] Update affected rows: {cursor.rowcount}")
            else:
                # Insert new
                print(f"[SIGNATURE UPDATE] Inserting new record")
                cursor.execute(
                    """
                    INSERT INTO grade_sheet_signatures 
                    (class_id, submitted_by_name, submitted_by_title,
                     checked_by_name, checked_by_title,
                     countersigned_by_name, countersigned_by_title,
                     noted_by_name, noted_by_title)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                    (
                        class_id,
                        data.get("submitted_by_name"),
                        data.get("submitted_by_title"),
                        data.get("checked_by_name"),
                        data.get("checked_by_title"),
                        data.get("countersigned_by_name"),
                        data.get("countersigned_by_title"),
                        data.get("noted_by_name"),
                        data.get("noted_by_title"),
                    ),
                )
                print(f"[SIGNATURE UPDATE] Insert affected rows: {cursor.rowcount}")

            # COMMIT THE TRANSACTION
            print(f"[SIGNATURE UPDATE] Committing transaction...")
            conn.commit()
            print(f"[SIGNATURE UPDATE] Transaction committed successfully")
            cursor.close()
            conn.close()

            return (
                jsonify(
                    {"success": True, "message": "Signatures updated successfully"}
                ),
                200,
            )

    except Exception as e:
        if "conn" in locals() and conn:
            conn.rollback()
            print(f"[SIGNATURE UPDATE] Transaction rolled back due to error: {e}")
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        if "cursor" in locals() and cursor:
            try:
                cursor.close()
            except:
                pass
        if "conn" in locals() and conn:
            try:
                conn.close()
            except:
                pass
