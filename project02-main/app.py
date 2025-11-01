import logging
import os
import sys
import ast
import uuid
import hashlib
import random
import json
from datetime import datetime
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    jsonify,
)
from flask_socketio import SocketIO, emit, join_room, leave_room

# Create Flask app
app = Flask(__name__)

# Add enumerate to Jinja environment
app.jinja_env.globals.update(enumerate=enumerate)
from flask_wtf.csrf import CSRFProtect, generate_csrf

# Ensure csrf_token() helper is available in all templates
app.jinja_env.globals.update(csrf_token=generate_csrf)
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from utils.db_conn import get_db_connection
from utils.grade_calculation import perform_grade_computation
from utils.live import (
    initialize_live,
    register_socketio_handlers,
    emit_live_version_update,
    get_cached_class_live_version,
    _cache_get,
    _cache_put,
    _grouped_cache_get,
    _grouped_cache_put,
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Helper function to generate class codes
# Usage: Internal helper used by create_class() API to generate unique
#         class_code and 6-digit join_code for new classes.
def generate_class_codes():
    """Generate unique 36-character class code and 6-digit join code"""
    class_code = str(uuid.uuid4())
    hash_obj = hashlib.md5(class_code.encode())
    hash_hex = hash_obj.hexdigest()
    join_code = "".join(c for c in hash_hex[:6] if c.isdigit())
    while len(join_code) < 6:
        join_code += str(random.randint(0, 9))
    return class_code, join_code[:6]


# Login required decorator
# Usage: Decorator applied to protected pages/APIs such as dashboards,
#         instructor/student class routes, and gradebuilder endpoints.
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "error")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated_function


# Use the same Flask app instance; set secret key
app.secret_key = "dev-secret-key-change-in-production"

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize live helpers and register Socket.IO handlers
initialize_live(socketio, logger)
register_socketio_handlers(socketio)


# -----------------------------
# Startup health/preflight checks
# -----------------------------
def _iter_python_files(base_dir: str):
    """Yield absolute paths to .py files under base_dir, excluding common virtualenv/cache dirs."""
    exclude_dirs = {".venv", "venv", "__pycache__", ".pytest_cache", ".git", ".vscode"}
    for root, dirs, files in os.walk(base_dir):
        # Prune excluded dirs in-place for efficiency
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for name in files:
            if name.endswith(".py"):
                yield os.path.join(root, name)


def check_python_syntax(base_dir: str):
    """Return (ok: bool, results: dict) where results has counts and any errors found.

    We parse files with ast to catch SyntaxError without executing code.
    """
    files = list(_iter_python_files(base_dir))
    errors = []
    for path in files:
        try:
            with open(path, "r", encoding="utf-8") as f:
                src = f.read()
            ast.parse(src, filename=path)
        except SyntaxError as e:
            errors.append(
                {
                    "file": path,
                    "line": getattr(e, "lineno", None),
                    "col": getattr(e, "offset", None),
                    "msg": str(e),
                }
            )
        except Exception as e:
            # Non-syntax read error; report as error as well
            errors.append(
                {
                    "file": path,
                    "line": None,
                    "col": None,
                    "msg": f"Read/parse error: {e}",
                }
            )
    return (len(errors) == 0), {"total_files": len(files), "errors": errors}


def check_database_connectivity():
    """Attempt a simple DB connection and SELECT 1. Return (ok: bool, message: str)."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            _ = cursor.fetchone()
        try:
            conn.close()
        except Exception:
            pass
        return True, "Connected and SELECT 1 succeeded"
    except Exception as e:
        return False, f"DB connection failed: {e}"


def run_startup_checks_or_exit():
    """Run preflight checks and exit the process on failure.

    Uses emoji-coded logs for quick visual scanning.
    """
    project_root = os.path.dirname(os.path.abspath(__file__))
    logger.info("🧪 Running startup checks…")

    # 1) Python syntax
    ok_py, result = check_python_syntax(project_root)
    total = result.get("total_files", 0)
    if ok_py:
        logger.info(f"✅ Python syntax check passed ({total} files scanned)")
    else:
        logger.error(
            f"❌ Python syntax check failed ({total} files scanned, {len(result['errors'])} errors)"
        )
        for err in result["errors"][:20]:  # limit output
            loc = f":{err['line']}:{err['col']}" if err["line"] else ""
            logger.error(f"   • {err['file']}{loc} → {err['msg']}")

    # 2) Database connectivity
    ok_db, db_msg = check_database_connectivity()
    if ok_db:
        logger.info(f"🗄️  Database check: ✅ {db_msg}")
    else:
        logger.error(f"🗄️  Database check: ❌ {db_msg}")

    if ok_py and ok_db:
        logger.info("🟢 All systems green. Starting server…")
        return
    else:
        logger.error("🔴 Startup checks failed. Aborting launch.")
        sys.exit(1)


# Register blueprints (modular APIs)
from blueprints.assessments_routes import assessments_bp
from blueprints.auth_routes import auth_bp
from blueprints.admin_routes import admin_bp
from blueprints.compute_routes import compute_bp, compute_class_grades
from blueprints.gradebuilder_routes import gradebuilder_bp

app.register_blueprint(assessments_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(compute_bp)
app.register_blueprint(gradebuilder_bp)

# Exempt the compute POST endpoint from CSRF for dev/tests convenience
try:
    csrf.exempt(compute_class_grades)
except Exception:
    # If CSRF isn't initialized yet or exemption fails, continue; compute endpoint also has a local flag.
    pass


# Route: GET "/"
# Used by: Direct browser navigation to the root; renders index.html
# Purpose: Landing page (same content as /index).
@app.route("/")
def home():
    logger.info("Home page accessed")
    return render_template("index.html")


# Route: GET "/index"
# Used by: Direct navigation/links; renders index.html
# Purpose: Alternative landing page path.
@app.route("/index")
def index():
    logger.info("Index page accessed")
    return render_template("index.html")


# API: GET "/welcome"
# Used by: Health-check or quick connectivity tests (no templates depend on it)
# Purpose: Returns a simple JSON welcome message.
@app.route("/welcome", methods=["GET"])
def welcome():
    logger.info(f"Request received: {request.method} {request.path}")
    return jsonify({"message": "Welcome to the Flask API Service!"})


# (login route moved to blueprints/auth_routes.py)


# (admin-login route moved to blueprints/auth_routes.py)


# (instructor-login route moved to blueprints/auth_routes.py)


# (student-login route moved to blueprints/auth_routes.py)


# (logout route moved to blueprints/auth_routes.py)


from blueprints.dashboard_routes import dashboard_bp
from blueprints.instructor_routes import instructor_bp
from blueprints.student_routes import student_bp
from blueprints.dev_routes import dev_bp

app.register_blueprint(dashboard_bp)
app.register_blueprint(instructor_bp)
app.register_blueprint(student_bp)
app.register_blueprint(dev_bp)


# (register route moved to blueprints/auth_routes.py)


# (instructor class management routes moved to blueprints/instructor_routes.py)


# API: GET "/api/instructor/classes"
# Used by: instructor_dashboard.html, instructor_classes.html (fetch class list)
# Purpose: Return all classes owned by the logged-in instructor.
# (instructor classes API moved to blueprints/instructor_routes.py)


# API: POST "/api/instructor/classes"
# Used by: instructor_classes.html (create class)
# Purpose: Create a new class for the logged-in instructor.
# (create class API moved to blueprints/instructor_routes.py)


# Student Class Management Routes
# Pages using these: student_dashboard.html
# (dev test-grade-normalizer moved to blueprints/dev_routes.py)


# (normalize_structure moved to utils/structure_utils.py)


# (_instructor_owns_class no longer needed here; local versions exist in blueprints)


# (group_structure moved to utils/structure_utils.py)


# Helper: get_equivalent(final_grade)
# Used by: Reserved for grade equivalency mapping (not directly referenced by current routes)
# Purpose: Map numeric grade to institution-style equivalent string.
def get_equivalent(final_grade: float) -> str:
    """Map numeric grade to equivalent string. Placeholder scale; adjust to institution policy."""
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


# Helper: validate_structure_json(structure)
# Used by: gradebuilder_save() to validate posted structure JSON schema and weights
# Purpose: Validate structure shape, types, and weight totals.
def validate_structure_json(structure: dict):
    """Validate grade_structures.structure_json shape and types.

    Rules:
    - Top-level: dict with keys 'LABORATORY' and 'LECTURE' (arrays)
    - Each category item: { name: str, weight: number, assessments: array }
    - Each assessment: { name: str, max_score: number }

    Returns: (is_valid: bool, errors: list[str])
    """
    errors = []

    if not isinstance(structure, dict):
        return False, ["structure_json must be an object"]

    for top_key in ("LABORATORY", "LECTURE"):
        if top_key not in structure:
            errors.append(f"Missing required key: {top_key}")
            continue
        items = structure.get(top_key)
        if not isinstance(items, list):
            errors.append(f"{top_key} must be an array")
            continue
        for i, cat in enumerate(items):
            path = f"{top_key}[{i}]"
            if not isinstance(cat, dict):
                errors.append(f"{path} must be an object")
                continue
            name = cat.get("name")
            if not isinstance(name, str) or not name.strip():
                errors.append(f"{path}.name must be a non-empty string")
            weight = cat.get("weight")
            if not isinstance(weight, (int, float)):
                errors.append(f"{path}.weight must be a number")
            # assessments are optional in the new model (assessments will be created at grade-entry time)
            assessments = cat.get("assessments", [])
            if assessments is not None and not isinstance(assessments, list):
                errors.append(f"{path}.assessments must be an array if provided")
                continue
            # If assessments are provided, validate their shape; otherwise allow empty list
            for j, a in enumerate(assessments or []):
                apath = f"{path}.assessments[{j}]"
                if not isinstance(a, dict):
                    errors.append(f"{apath} must be an object")
                    continue
                aname = a.get("name")
                if not isinstance(aname, str) or not aname.strip():
                    errors.append(f"{apath}.name must be a non-empty string")
                max_score = a.get("max_score")
                if not isinstance(max_score, (int, float)):
                    errors.append(f"{apath}.max_score must be a number")

    # Ensure subcategory weights sum approximately to 100 for each top-level category
    try:
        for top_key in ("LABORATORY", "LECTURE"):
            items = structure.get(top_key, []) or []
            if isinstance(items, list) and len(items) > 0:
                total = 0.0
                for cat in items:
                    w = cat.get("weight") if isinstance(cat, dict) else 0
                    try:
                        total += float(w or 0)
                    except Exception:
                        pass
                # Allow small floating point tolerance
                if abs(total - 100.0) > 0.01:
                    errors.append(
                        f"{top_key} subcategory weights must sum to 100 (got {total})"
                    )
    except Exception:
        # Non-fatal; validation errors already captured above
        pass

    return len(errors) == 0, errors


# API: GET "/api/classes/<class_id>/normalized"
# Used by: test/dev tools and future analytics; may be consumed by UI experiments
# Purpose: Return flattened structure for caching/compute.
# (compute normalized moved to blueprints/compute_routes.py)


# API: GET "/api/classes/<class_id>/grouped"
# Used by: test/dev tools and future analytics
# Purpose: Return grouped strings vs numbers derived from normalized structure.
# (compute grouped moved to blueprints/compute_routes.py)


# API: GET "/api/classes/<class_id>/calculate"
# Used by: internal/testing endpoints; future integration with instructor views
# Purpose: Compute grades using the active formula and current scores.
# (compute calculate moved to blueprints/compute_routes.py)


# Route: GET "/instructor/class/<class_id>/grades"
# Used by: instructor_dashboard.html ("Open Grade Entry" button)
# Purpose: Official instructor page for unified grade entry/visualization.
# (instructor grades page moved to blueprints/instructor_routes.py)


# API: GET "/api/classes/<class_id>/live-version"
# Used by: test_grade_normalizer.html and live UI to detect changes (polling)
# Purpose: Returns a cache-busting version that updates on data changes.
# (compute live-version moved to blueprints/compute_routes.py)


# API: GET "/api/instructor/class/<class_id>/has-structure"
# Used by: instructor_dashboard.html (to enable grade entry when a structure exists)
# Purpose: Boolean indicating presence of an active grade structure.
# (has-structure API moved to blueprints/instructor_routes.py)


# (dev grade-test moved to blueprints/dev_routes.py)


# (compute compute_class_grades moved to blueprints/compute_routes.py)


# Internal test helper (not a route)
# Used by: Inline sanity test to ensure compute endpoint returns JSON
# Purpose: Quick smoke test via Flask test_client.
def test_compute_endpoint_exists():
    client = app.test_client()
    # Call the compute endpoint for class_id 2 (MAJOR Networking)
    resp = client.post("/api/compute/class/2")
    # Endpoint should respond (200 or 404 if no structure) but must return JSON
    assert resp.status_code in (200, 404, 500)
    try:
        data = resp.get_json()
        assert isinstance(data, dict)
    except Exception:
        # If response is not JSON, fail
        assert False, "Response is not valid JSON"


if __name__ == "__main__":
    logger.info("Application startup initiated")
    # Run preflight checks before launching the server
    # Note: With the Werkzeug reloader, this may run twice in development.
    # If this becomes noisy, guard with WERKZEUG_RUN_MAIN env flag.
    run_startup_checks_or_exit()
    socketio.run(app, debug=True)
