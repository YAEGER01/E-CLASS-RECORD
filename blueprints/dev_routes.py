import json
import logging
import subprocess
import os
import sys
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    session,
)
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


@dev_bp.route("/terminal", endpoint="terminal")
def terminal():
    """Web-based terminal for debugging"""
    # Simple auth check - only allow if admin or in dev mode
    if session.get("role") != "admin" and not os.environ.get("FLASK_DEBUG"):
        flash("Access denied. Admin access required.", "error")
        return redirect(url_for("auth.login"))

    return render_template("dev_terminal.html")


@dev_bp.route("/terminal/execute", methods=["POST"], endpoint="terminal_execute")
def terminal_execute():
    """Execute terminal commands"""
    # Security check
    if session.get("role") != "admin" and not os.environ.get("FLASK_DEBUG"):
        return jsonify({"error": "Access denied"}), 403

    try:
        data = request.get_json()
        command = data.get("command", "").strip()

        if not command:
            return jsonify({"output": "", "error": None})

        # Security: Block dangerous commands
        blocked_commands = ["rm -rf", "del /f", "format", "shutdown", "reboot", "mkfs"]
        if any(blocked in command.lower() for blocked in blocked_commands):
            return jsonify(
                {"output": "", "error": "⚠️ Command blocked for safety reasons"}
            )

        # Special built-in commands
        if command.startswith("cd "):
            try:
                path = command[3:].strip()
                os.chdir(path)
                return jsonify(
                    {"output": f"Changed directory to: {os.getcwd()}", "error": None}
                )
            except Exception as e:
                return jsonify(
                    {"output": "", "error": f"Error changing directory: {str(e)}"}
                )

        if command == "pwd":
            return jsonify({"output": os.getcwd(), "error": None})

        if command == "cls" or command == "clear":
            return jsonify({"output": "CLEAR_SCREEN", "error": None})

        # Execute command
        try:
            # Use shell=True for Windows to handle built-in commands
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,  # 30 second timeout
                cwd=os.getcwd(),
            )

            output = result.stdout
            if result.stderr:
                output += f"\n{result.stderr}"

            return jsonify(
                {
                    "output": output or "(no output)",
                    "error": (
                        None
                        if result.returncode == 0
                        else f"Exit code: {result.returncode}"
                    ),
                }
            )

        except subprocess.TimeoutExpired:
            return jsonify({"output": "", "error": "⏱️ Command timed out (30s limit)"})
        except Exception as e:
            return jsonify({"output": "", "error": f"Execution error: {str(e)}"})

    except Exception as e:
        logger.error(f"Terminal execute error: {str(e)}")
        return jsonify({"output": "", "error": f"Server error: {str(e)}"}), 500


@dev_bp.route("/terminal/info", endpoint="terminal_info")
def terminal_info():
    """Get system information"""
    if session.get("role") != "admin" and not os.environ.get("FLASK_DEBUG"):
        return jsonify({"error": "Access denied"}), 403

    try:
        info = {
            "python_version": sys.version,
            "cwd": os.getcwd(),
            "platform": sys.platform,
            "executable": sys.executable,
        }
        return jsonify(info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@dev_bp.route("/terminal/logs", methods=["GET"], endpoint="terminal_logs")
def terminal_logs():
    """Return the latest application logs for display in the web terminal."""
    if session.get("role") != "admin" and not os.environ.get("FLASK_DEBUG"):
        return jsonify({"error": "Access denied"}), 403

    # Default log file path
    log_path = os.path.join(os.getcwd(), "app.log")
    max_bytes = 100 * 1024  # read up to last 100KB

    try:
        if not os.path.exists(log_path):
            return jsonify({"log": "(log file not found: app.log)"})

        size = os.path.getsize(log_path)
        start = max(0, size - max_bytes)
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            if start > 0:
                f.seek(start)
            content = f.read()

        # If we started mid-file, drop a potentially partial first line
        if start > 0:
            content = "\n".join(content.splitlines()[1:])

        return jsonify({"log": content})
    except Exception as e:
        return jsonify({"log": "", "error": f"Failed to read logs: {str(e)}"}), 500
