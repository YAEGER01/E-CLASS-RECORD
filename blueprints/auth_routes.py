import logging
import os
import secrets
import time
import ipaddress
import hashlib
import hmac
import json
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from itsdangerous import BadSignature, URLSafeSerializer
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from utils.db_conn import get_db_connection
from utils.email_service import email_service
from utils.rate_limiter import get_login_limiter
from utils.auth_utils import validate_password_policy
from functools import wraps

logger = logging.getLogger(__name__)

# Configuration for file uploads
UPLOAD_FOLDER = "static/uploads/student_photos"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# Blueprint: auth (no url_prefix to preserve original paths)
auth_bp = Blueprint("auth", __name__)


def _get_int_env(name: str, default: int) -> int:
    raw = (os.environ.get(name) or "").strip()
    if not raw:
        return default
    try:
        return max(1, int(raw))
    except Exception:
        logger.warning(f"Invalid integer for {name}: {raw!r}. Using default {default}")
        return default


def _get_bool_env(name: str, default: bool) -> bool:
    raw = (os.environ.get(name) or "").strip().lower()
    if not raw:
        return default
    if raw in {"1", "true", "yes", "on"}:
        return True
    if raw in {"0", "false", "no", "off"}:
        return False
    logger.warning(f"Invalid boolean for {name}: {raw!r}. Using default {default}")
    return default


def _get_mfa_required_roles() -> set[str]:
    configured = (os.environ.get("MFA_REQUIRED_ROLES") or "admin,instructor").strip()
    roles = {r.strip().lower() for r in configured.split(",") if r.strip()}
    return roles or {"admin", "instructor"}


MFA_ENABLED = os.environ.get("MFA_ENABLED", "false").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
MFA_REQUIRED_ROLES = _get_mfa_required_roles()
MFA_CODE_TTL_SECONDS = _get_int_env("MFA_CODE_TTL_SECONDS", 300)
MFA_MAX_ATTEMPTS = _get_int_env("MFA_MAX_ATTEMPTS", 5)
MFA_RESEND_COOLDOWN_SECONDS = _get_int_env("MFA_RESEND_COOLDOWN_SECONDS", 30)
MFA_TRUST_DEVICE_ENABLED = _get_bool_env("MFA_TRUST_DEVICE_ENABLED", True)
MFA_TRUST_DAYS = _get_int_env("MFA_TRUST_DAYS", 14)
MFA_TRUST_COOKIE_NAME = (
    os.environ.get("MFA_TRUST_COOKIE_NAME") or "mfa_trust_token"
).strip() or "mfa_trust_token"
MFA_TRUST_BIND_USER_AGENT = _get_bool_env("MFA_TRUST_BIND_USER_AGENT", True)

CAPTCHA_ENABLED = os.environ.get("CAPTCHA_ENABLED", "false").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
CF_TURNSTILE_SITE_KEY = (os.environ.get("CF_TURNSTILE_SITE_KEY") or "").strip()
CF_TURNSTILE_SECRET_KEY = (os.environ.get("CF_TURNSTILE_SECRET_KEY") or "").strip()
CAPTCHA_FAIL_OPEN_DEVELOPMENT = os.environ.get(
    "CAPTCHA_FAIL_OPEN_DEVELOPMENT", "true"
).strip().lower() in {"1", "true", "yes", "on"}


def _captcha_is_enforced() -> bool:
    return CAPTCHA_ENABLED and bool(CF_TURNSTILE_SITE_KEY and CF_TURNSTILE_SECRET_KEY)


@auth_bp.app_context_processor
def inject_captcha_context():
    return {
        "captcha_enabled": _captcha_is_enforced(),
        "cf_turnstile_site_key": CF_TURNSTILE_SITE_KEY,
    }


def _verify_turnstile_for_current_request(flow_name: str):
    if not _captcha_is_enforced():
        return True, ""

    token = (request.form.get("cf-turnstile-response") or "").strip()
    if not token:
        return False, "Please complete the CAPTCHA challenge."

    payload = urllib.parse.urlencode(
        {
            "secret": CF_TURNSTILE_SECRET_KEY,
            "response": token,
            "remoteip": get_client_ip(),
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        "https://challenges.cloudflare.com/turnstile/v0/siteverify",
        data=payload,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            result = json.loads(response.read().decode("utf-8"))
    except Exception as e:
        logger.error(f"Turnstile verification error for {flow_name}: {e}")
        is_dev = os.environ.get("FLASK_ENV", "development") != "production"
        if is_dev and CAPTCHA_FAIL_OPEN_DEVELOPMENT:
            logger.warning(f"Turnstile fail-open in development for {flow_name}.")
            return True, ""
        return False, "CAPTCHA service unavailable. Please try again."

    if result.get("success"):
        return True, ""

    error_codes = result.get("error-codes") or []
    logger.warning(
        f"Turnstile verification failed for {flow_name}: {','.join(error_codes)}"
    )
    return False, "CAPTCHA verification failed. Please try again."


def _role_login_endpoint(role: str) -> str:
    if role == "admin":
        return "auth.admin_login"
    if role == "instructor":
        return "auth.instructor_login"
    return "auth.login"


def _is_mfa_required(role: str) -> bool:
    return MFA_ENABLED and role in MFA_REQUIRED_ROLES


def _get_mfa_trust_serializer() -> URLSafeSerializer | None:
    secret = (os.environ.get("SECRET_KEY") or "").strip()
    if not secret:
        return None
    return URLSafeSerializer(secret_key=secret, salt="mfa-trust-cookie-v1")


def _mfa_user_agent_fingerprint() -> str:
    user_agent = (request.headers.get("User-Agent") or "").strip()
    if not user_agent:
        return ""
    return hashlib.sha256(user_agent.encode("utf-8")).hexdigest()[:24]


def _has_valid_mfa_trust_cookie(user_id: int, role: str) -> bool:
    if not MFA_TRUST_DEVICE_ENABLED:
        logger.debug("MFA trust device disabled")
        return False

    raw_token = (request.cookies.get(MFA_TRUST_COOKIE_NAME) or "").strip()
    if not raw_token:
        logger.debug(f"No trust cookie found (looking for {MFA_TRUST_COOKIE_NAME})")
        return False

    logger.debug(f"Found trust cookie for user_id={user_id}, role={role}")

    serializer = _get_mfa_trust_serializer()
    if serializer is None:
        logger.warning("MFA trust serializer is None (SECRET_KEY not set)")
        return False

    try:
        payload = serializer.loads(raw_token)
        logger.debug(f"Trust cookie deserialized: {payload}")
    except BadSignature:
        logger.warning("Trust cookie failed signature verification")
        return False
    except Exception as e:
        logger.warning(f"Trust cookie deserialization error: {e}")
        return False

    try:
        payload_user_id = int(payload.get("uid") or 0)
        payload_exp = int(payload.get("exp") or 0)
    except Exception as e:
        logger.warning(f"Trust cookie payload extraction error: {e}")
        return False

    if payload_user_id != int(user_id):
        logger.debug(f"Trust cookie user_id mismatch: {payload_user_id} != {user_id}")
        return False
    if (payload.get("role") or "") != role:
        logger.debug(f"Trust cookie role mismatch: {payload.get('role')} != {role}")
        return False

    now = int(time.time())
    if payload_exp <= now:
        logger.debug(f"Trust cookie expired: {payload_exp} <= {now}")
        return False

    if MFA_TRUST_BIND_USER_AGENT:
        expected_ua = payload.get("ua") or ""
        current_ua = _mfa_user_agent_fingerprint()
        if not expected_ua or expected_ua != current_ua:
            logger.debug(
                f"Trust cookie UA binding failed: {expected_ua} != {current_ua}"
            )
            return False

    logger.info(
        f"Trust cookie validated successfully for user_id={user_id}, role={role}"
    )
    return True


def _set_mfa_trust_cookie(response, user_id: int, role: str):
    if not MFA_TRUST_DEVICE_ENABLED:
        logger.debug("MFA trust device disabled, skipping cookie")
        return

    serializer = _get_mfa_trust_serializer()
    if serializer is None:
        logger.warning(
            "Cannot set trust cookie: serializer is None (SECRET_KEY not set)"
        )
        return

    max_age = max(1, MFA_TRUST_DAYS) * 24 * 60 * 60
    payload = {
        "uid": int(user_id),
        "role": role,
        "exp": int(time.time()) + max_age,
    }
    if MFA_TRUST_BIND_USER_AGENT:
        payload["ua"] = _mfa_user_agent_fingerprint()

    token = serializer.dumps(payload)
    logger.info(
        f"Setting MFA trust cookie for user_id={user_id}, role={role}, max_age={max_age}s, ua_binding={MFA_TRUST_BIND_USER_AGENT}"
    )
    response.set_cookie(
        MFA_TRUST_COOKIE_NAME,
        token,
        max_age=max_age,
        httponly=True,
        secure=request.is_secure,
        samesite="Lax",
        path="/",
    )


def _mask_email(email: str) -> str:
    if not email or "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        local_mask = "*" * len(local)
    else:
        local_mask = local[0] + ("*" * (len(local) - 2)) + local[-1]
    return f"{local_mask}@{domain}"


def _hash_mfa_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def _generate_mfa_code() -> str:
    return f"{secrets.randbelow(1000000):06d}"


def _get_user_email_for_mfa(user_id: int, role: str) -> str | None:
    try:
        with get_db_connection().cursor() as cursor:
            if role == "instructor":
                cursor.execute(
                    """
                    SELECT pi.email
                    FROM instructors i
                    JOIN personal_info pi ON i.personal_info_id = pi.id
                    WHERE i.user_id = %s
                    LIMIT 1
                    """,
                    (user_id,),
                )
                row = cursor.fetchone()
                return row.get("email") if row else None

            if role == "student":
                cursor.execute(
                    """
                    SELECT pi.email
                    FROM students s
                    JOIN personal_info pi ON s.personal_info_id = pi.id
                    WHERE s.user_id = %s
                    LIMIT 1
                    """,
                    (user_id,),
                )
                row = cursor.fetchone()
                return row.get("email") if row else None

            if role == "admin":
                # Admin accounts may also be represented in instructors table.
                cursor.execute(
                    """
                    SELECT pi.email
                    FROM instructors i
                    JOIN personal_info pi ON i.personal_info_id = pi.id
                    WHERE i.user_id = %s
                    LIMIT 1
                    """,
                    (user_id,),
                )
                row = cursor.fetchone()
                return row.get("email") if row else None
    except Exception as e:
        logger.error(
            f"Failed to resolve MFA email for user_id={user_id}, role={role}: {e}"
        )

    return None


def _create_mfa_challenge(user: dict, role: str, next_endpoint: str):
    if not _is_mfa_required(role):
        return None

    if _has_valid_mfa_trust_cookie(int(user["id"]), role):
        logger.info(
            f"Skipping MFA challenge for trusted device user_id={user['id']} role={role}"
        )
        return None

    email = _get_user_email_for_mfa(user["id"], role)
    if not email:
        flash(
            "MFA is required for this account, but no email is configured. Please contact an administrator.",
            "error",
        )
        return redirect(url_for(_role_login_endpoint(role)))

    code = _generate_mfa_code()
    sent = email_service.send_mfa_code_email(
        recipient_email=email,
        recipient_name=user.get("school_id", "User"),
        code=code,
        expiry_minutes=max(1, MFA_CODE_TTL_SECONDS // 60),
        role=role,
    )
    if not sent:
        flash(
            "Unable to deliver MFA code at the moment. Please try again.",
            "error",
        )
        return redirect(url_for(_role_login_endpoint(role)))

    now = int(time.time())
    session["mfa_pending"] = {
        "user_id": int(user["id"]),
        "school_id": user.get("school_id"),
        "role": role,
        "email": email,
        "code_hash": _hash_mfa_code(code),
        "expires_at": now + MFA_CODE_TTL_SECONDS,
        "attempts_left": MFA_MAX_ATTEMPTS,
        "last_sent_at": now,
        "next_endpoint": next_endpoint,
    }
    return redirect(url_for("auth.mfa_verify"))


def _complete_mfa_login(pending: dict):
    role = pending.get("role")
    user_id = pending.get("user_id")
    school_id = pending.get("school_id")

    session.pop("mfa_pending", None)
    session["user_id"] = user_id
    session["school_id"] = school_id
    session["role"] = role
    session.permanent = True

    if role == "instructor":
        try:
            with get_db_connection().cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM instructors WHERE user_id = %s", (user_id,)
                )
                instr = cursor.fetchone()
                if instr:
                    session["instructor_id"] = instr["id"]
        except Exception as e:
            logger.error(f"Failed to resolve instructor_id during MFA completion: {e}")

    next_endpoint = pending.get("next_endpoint") or "home"
    return redirect(url_for(next_endpoint))


def _get_pending_mfa() -> dict | None:
    pending = session.get("mfa_pending")
    if not isinstance(pending, dict):
        return None
    required = {
        "user_id",
        "school_id",
        "role",
        "email",
        "code_hash",
        "expires_at",
        "attempts_left",
        "next_endpoint",
    }
    if not required.issubset(set(pending.keys())):
        session.pop("mfa_pending", None)
        return None
    return pending


def get_client_ip():
    """Get the client's IP from normalized request context.

    Forwarded headers are only trusted when ProxyFix is enabled in app.py.
    """
    raw_ip = request.remote_addr or request.environ.get("REMOTE_ADDR") or "127.0.0.1"
    try:
        return str(ipaddress.ip_address(raw_ip))
    except ValueError:
        logger.warning(f"Invalid client IP address received: {raw_ip!r}")
        return "127.0.0.1"


def check_rate_limit(username, role):
    """
    Check if user is rate limited.

    Returns:
        tuple: (is_allowed: bool, message: str)
    """
    limiter = get_login_limiter()
    ip_address = get_client_ip()

    allowed, message, remaining = limiter.check_rate_limit(username, ip_address, role)
    return allowed, message


# Route: GET "/login"
# Used by: login.html (rendered by this route); many protected routes redirect here on auth failure
# Purpose: Role selection and entry point to admin/instructor/student login pages.
@auth_bp.route("/login", endpoint="login")
def login():
    """Display the role selection page (landing page with login options)"""
    logger.info("Login role selection page accessed")
    return render_template("login.html")


# Route: GET/POST "/admin-login"
# Used by: adminlogin.html (form posts here); redirects from protected admin pages when not authenticated
# Purpose: Authenticate admin users; sets session and redirects to /admin-dashboard.
@auth_bp.route("/admin-login", methods=["GET", "POST"], endpoint="admin_login")
def admin_login():
    role = "admin"
    client_ip = get_client_ip()
    limiter = get_login_limiter()

    def get_session_lock_remaining():
        """Get remaining admin lock time from session and clear expired values."""
        locked_until = session.get("admin_login_locked_until")
        if not locked_until:
            return 0

        try:
            remaining_seconds = int(locked_until) - int(time.time())
        except (TypeError, ValueError):
            session.pop("admin_login_locked_until", None)
            return 0

        if remaining_seconds <= 0:
            session.pop("admin_login_locked_until", None)
            return 0

        return remaining_seconds

    def set_session_lock(remaining_seconds):
        """Store admin lock expiration in session for refresh/back persistence."""
        if remaining_seconds > 0:
            session["admin_login_locked_until"] = int(time.time()) + int(
                remaining_seconds
            )

    def get_ip_lock_remaining():
        """Get current lock remaining for this IP/role from login_tracker."""
        try:
            now = int(time.time())
            max_remaining = 0
            with get_db_connection().cursor() as cursor:
                cursor.execute(
                    """
                    SELECT last_attempt_at
                    FROM login_tracker
                    WHERE ip_address = %s AND user_role = %s AND is_blocked = 1
                    """,
                    (client_ip, role),
                )
                blocked_rows = cursor.fetchall() or []

            for row in blocked_rows:
                last_attempt_at = int(row.get("last_attempt_at") or 0)
                remaining = limiter.lock_duration - (now - last_attempt_at)
                if remaining > max_remaining:
                    max_remaining = remaining

            return max_remaining if max_remaining > 0 else 0
        except Exception as e:
            logger.error(f"Error reading IP lock state: {str(e)}")
            return 0

    def lock_redirect(remaining_seconds):
        minutes = remaining_seconds // 60
        seconds = remaining_seconds % 60
        flash(
            f"Too many failed attempts. Please try again in {minutes}m {seconds}s",
            "error",
        )
        return redirect(
            url_for("auth.admin_login", locked=1, seconds=remaining_seconds)
        )

    ip_remaining = get_ip_lock_remaining()

    if request.method == "POST":
        school_id = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        captcha_ok, captcha_message = _verify_turnstile_for_current_request(
            "admin_login"
        )
        if not captcha_ok:
            flash(captcha_message, "error")
            return redirect(url_for("auth.admin_login"))

        logger.info(
            f"Admin login attempt for school ID: {school_id} from IP: {client_ip}"
        )

        # Enforce DB-backed IP lock first so refresh/cache/session changes cannot bypass lock.
        if ip_remaining > 0:
            set_session_lock(ip_remaining)
            return lock_redirect(ip_remaining)

        # Enforce persisted lock state even after refresh/navigation.
        session_remaining = get_session_lock_remaining()
        if session_remaining > 0:
            return lock_redirect(session_remaining)

        if not school_id or not password:
            logger.warning("Admin login failed: Missing credentials")
            flash("Please enter both school ID and password.", "error")
            return redirect(url_for("auth.admin_login"))

        # Check rate limit before processing
        allowed, message, remaining = limiter.check_rate_limit(
            school_id, client_ip, role
        )
        if not allowed:
            set_session_lock(remaining)
            flash(message, "error")
            # Redirect to login page with locked status
            return redirect(url_for("auth.admin_login", locked=1, seconds=remaining))

        # Find user using raw SQL
        try:
            with get_db_connection().cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE school_id = %s", (school_id,))
                user = cursor.fetchone()
        except Exception as e:
            logger.error(f"Database error during admin user lookup: {str(e)}")
            flash("An error occurred. Please try again.", "error")
            return redirect(url_for("auth.admin_login"))

        if not user:
            logger.warning(f"Admin login failed: User {school_id} not found")
            # Record failed attempt
            limiter.process_fail(school_id, client_ip, role)
            allowed, message, remaining = limiter.check_rate_limit(
                school_id, client_ip, role
            )
            if not allowed:
                set_session_lock(remaining)
                flash(message, "error")
                return redirect(
                    url_for("auth.admin_login", locked=1, seconds=remaining)
                )
            flash("Invalid admin credentials.", "error")
            return redirect(url_for("auth.admin_login"))

        # Check password
        if not check_password_hash(user["password_hash"], password):
            logger.warning(f"Admin login failed: Invalid password for user {school_id}")
            # Record failed attempt
            limiter.process_fail(school_id, client_ip, role)
            allowed, message, remaining = limiter.check_rate_limit(
                school_id, client_ip, role
            )
            if not allowed:
                set_session_lock(remaining)
                flash(message, "error")
                return redirect(
                    url_for("auth.admin_login", locked=1, seconds=remaining)
                )
            flash("Invalid admin credentials.", "error")
            return redirect(url_for("auth.admin_login"))

        # Check role
        if user["role"] != role:
            logger.warning(f"Admin login failed: Role mismatch for user {school_id}")
            # Record failed attempt
            limiter.process_fail(school_id, client_ip, role)
            allowed, message, remaining = limiter.check_rate_limit(
                school_id, client_ip, role
            )
            if not allowed:
                set_session_lock(remaining)
                flash(message, "error")
                return redirect(
                    url_for("auth.admin_login", locked=1, seconds=remaining)
                )
            flash("Invalid admin credentials.", "error")
            return redirect(url_for("auth.admin_login"))

        logger.info(f"Admin {school_id} logged in successfully")
        # Reset failed attempts on successful login
        limiter.process_success(school_id, client_ip, role)
        session.pop("admin_login_locked_until", None)

        mfa_redirect = _create_mfa_challenge(
            user,
            role,
            "dashboard.admin_dashboard",
        )
        if mfa_redirect is not None:
            return mfa_redirect

        # Login successful (no MFA required)
        session["user_id"] = user["id"]
        session["school_id"] = user["school_id"]
        session["role"] = user["role"]
        session.permanent = True

        return redirect(url_for("dashboard.admin_dashboard"))

    logger.info("Admin login page accessed")
    query_locked = request.args.get("locked") == "1"
    try:
        query_seconds = int(request.args.get("seconds") or 0)
    except ValueError:
        query_seconds = 0

    session_seconds = get_session_lock_remaining()
    remaining_seconds = max(
        session_seconds,
        query_seconds if query_locked else 0,
        ip_remaining,
    )

    if remaining_seconds > 0:
        set_session_lock(remaining_seconds)

    return render_template(
        "adminlogin.html", locked=remaining_seconds > 0, seconds=remaining_seconds
    )


# Route: GET/POST "/instructor-login"
# Used by: instructorlogin.html (form posts here); redirects from instructor-only pages when unauthenticated
# Purpose: Authenticate instructors; sets session and redirects to /instructor-dashboard.
@auth_bp.route(
    "/instructor-login", methods=["GET", "POST"], endpoint="instructor_login"
)
def instructor_login():
    role = "instructor"
    client_ip = get_client_ip()
    limiter = get_login_limiter()

    def get_session_lock_remaining():
        """Get remaining instructor lock time from session and clear expired values."""
        locked_until = session.get("instructor_login_locked_until")
        if not locked_until:
            return 0

        try:
            remaining_seconds = int(locked_until) - int(time.time())
        except (TypeError, ValueError):
            session.pop("instructor_login_locked_until", None)
            return 0

        if remaining_seconds <= 0:
            session.pop("instructor_login_locked_until", None)
            return 0

        return remaining_seconds

    def set_session_lock(remaining_seconds):
        """Store instructor lock expiration in session for refresh/back persistence."""
        if remaining_seconds > 0:
            session["instructor_login_locked_until"] = int(time.time()) + int(
                remaining_seconds
            )

    def get_ip_lock_remaining():
        """Get current lock remaining for this IP/role from login_tracker."""
        try:
            now = int(time.time())
            max_remaining = 0
            with get_db_connection().cursor() as cursor:
                cursor.execute(
                    """
                    SELECT last_attempt_at
                    FROM login_tracker
                    WHERE ip_address = %s AND user_role = %s AND is_blocked = 1
                    """,
                    (client_ip, role),
                )
                blocked_rows = cursor.fetchall() or []

            for row in blocked_rows:
                last_attempt_at = int(row.get("last_attempt_at") or 0)
                remaining = limiter.lock_duration - (now - last_attempt_at)
                if remaining > max_remaining:
                    max_remaining = remaining

            return max_remaining if max_remaining > 0 else 0
        except Exception as e:
            logger.error(f"Error reading instructor IP lock state: {str(e)}")
            return 0

    def lock_redirect(remaining_seconds):
        minutes = remaining_seconds // 60
        seconds = remaining_seconds % 60
        flash(
            f"Too many failed attempts. Please try again in {minutes}m {seconds}s",
            "error",
        )
        return redirect(
            url_for("auth.instructor_login", locked=1, seconds=remaining_seconds)
        )

    ip_remaining = get_ip_lock_remaining()

    if request.method == "POST":
        school_id = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        captcha_ok, captcha_message = _verify_turnstile_for_current_request(
            "instructor_login"
        )
        if not captcha_ok:
            flash(captcha_message, "error")
            return redirect(url_for("auth.instructor_login"))

        logger.info(
            f"Instructor login attempt for school ID: {school_id} from IP: {client_ip}"
        )

        # Enforce DB-backed IP lock first so refresh/cache/session changes cannot bypass lock.
        if ip_remaining > 0:
            set_session_lock(ip_remaining)
            return lock_redirect(ip_remaining)

        # Enforce persisted lock state even after refresh/navigation.
        session_remaining = get_session_lock_remaining()
        if session_remaining > 0:
            return lock_redirect(session_remaining)

        if not school_id or not password:
            logger.warning("Instructor login failed: Missing credentials")
            flash("Please enter both school ID and password.", "error")
            return redirect(url_for("auth.instructor_login"))

        # Check rate limit before processing
        allowed, message, remaining = limiter.check_rate_limit(
            school_id, client_ip, role
        )
        if not allowed:
            set_session_lock(remaining)
            flash(message, "error")
            # Redirect to login page with locked status
            return redirect(
                url_for("auth.instructor_login", locked=1, seconds=remaining)
            )

        # Find user using raw SQL
        try:
            with get_db_connection().cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE school_id = %s", (school_id,))
                user = cursor.fetchone()
        except Exception as e:
            logger.error(f"Database error during instructor user lookup: {str(e)}")
            flash("An error occurred. Please try again.", "error")
            return redirect(url_for("auth.instructor_login"))

        if not user:
            logger.warning(f"Instructor login failed: User {school_id} not found")
            # Record failed attempt
            limiter.process_fail(school_id, client_ip, role)
            allowed, message, remaining = limiter.check_rate_limit(
                school_id, client_ip, role
            )
            if not allowed:
                set_session_lock(remaining)
                flash(message, "error")
                return redirect(
                    url_for("auth.instructor_login", locked=1, seconds=remaining)
                )
            flash("Invalid instructor credentials.", "error")
            return redirect(url_for("auth.instructor_login"))

        # Check password
        if not check_password_hash(user["password_hash"], password):
            logger.warning(
                f"Instructor login failed: Invalid password for user {school_id}"
            )
            # Record failed attempt
            limiter.process_fail(school_id, client_ip, role)
            allowed, message, remaining = limiter.check_rate_limit(
                school_id, client_ip, role
            )
            if not allowed:
                set_session_lock(remaining)
                flash(message, "error")
                return redirect(
                    url_for("auth.instructor_login", locked=1, seconds=remaining)
                )
            flash("Invalid instructor credentials.", "error")
            return redirect(url_for("auth.instructor_login"))

        # Check role
        if user["role"] != role:
            logger.warning(
                f"Instructor login failed: Role mismatch for user {school_id}"
            )
            # Record failed attempt
            limiter.process_fail(school_id, client_ip, role)
            allowed, message, remaining = limiter.check_rate_limit(
                school_id, client_ip, role
            )
            if not allowed:
                set_session_lock(remaining)
                flash(message, "error")
                return redirect(
                    url_for("auth.instructor_login", locked=1, seconds=remaining)
                )
            flash("Invalid instructor credentials.", "error")
            return redirect(url_for("auth.instructor_login"))

        # Check if instructor is suspended
        try:
            with get_db_connection().cursor() as cursor:
                cursor.execute(
                    "SELECT status FROM instructors WHERE user_id = %s", (user["id"],)
                )
                instructor = cursor.fetchone()
        except Exception as e:
            logger.error(f"Database error during instructor status check: {str(e)}")
            flash("An error occurred. Please try again.", "error")
            return redirect(url_for("auth.instructor_login"))

        if instructor and instructor["status"] == "suspended":
            logger.warning(
                f"Instructor login failed: Account suspended for user {school_id}"
            )
            # Record failed attempt (suspended accounts still count as failed attempts)
            limiter.process_fail(school_id, client_ip, role)
            allowed, message, remaining = limiter.check_rate_limit(
                school_id, client_ip, role
            )
            if not allowed:
                set_session_lock(remaining)
                flash(message, "error")
                return redirect(
                    url_for("auth.instructor_login", locked=1, seconds=remaining)
                )
            flash(
                "Your instructor account has been suspended. Please contact an administrator.",
                "error",
            )
            return redirect(url_for("auth.instructor_login"))

        logger.info(f"Instructor {school_id} logged in successfully")
        # Reset failed attempts on successful login
        limiter.process_success(school_id, client_ip, role)
        session.pop("instructor_login_locked_until", None)

        mfa_redirect = _create_mfa_challenge(
            user,
            role,
            "dashboard.instructor_dashboard",
        )
        if mfa_redirect is not None:
            return mfa_redirect

        # Login successful (no MFA required)
        session["user_id"] = user["id"]
        session["school_id"] = user["school_id"]
        session["role"] = user["role"]
        session.permanent = True

        # Fetch and store instructor_id for this user
        with get_db_connection().cursor() as cursor:
            cursor.execute(
                "SELECT id FROM instructors WHERE user_id = %s", (user["id"],)
            )
            instr = cursor.fetchone()
            if instr:
                session["instructor_id"] = instr["id"]

        return redirect(url_for("dashboard.instructor_dashboard"))

    logger.info("Instructor login page accessed")
    query_locked = request.args.get("locked") == "1"
    try:
        query_seconds = int(request.args.get("seconds") or 0)
    except ValueError:
        query_seconds = 0

    session_seconds = get_session_lock_remaining()
    remaining_seconds = max(
        session_seconds,
        query_seconds if query_locked else 0,
        ip_remaining,
    )

    if remaining_seconds > 0:
        set_session_lock(remaining_seconds)

    return render_template(
        "instructorlogin.html", locked=remaining_seconds > 0, seconds=remaining_seconds
    )


# Route: GET/POST "/student-login"
# Used by: studentlogin.html (form posts here); redirects from student-only pages when unauthenticated
# Purpose: Authenticate students; sets session and redirects to /student-dashboard.
@auth_bp.route("/student-login", methods=["GET", "POST"], endpoint="student_login")
def student_login():
    role = "student"
    client_ip = get_client_ip()
    limiter = get_login_limiter()

    def get_session_lock_remaining():
        """Get remaining student lock time from session and clear expired values."""
        locked_until = session.get("student_login_locked_until")
        if not locked_until:
            return 0

        try:
            remaining_seconds = int(locked_until) - int(time.time())
        except (TypeError, ValueError):
            session.pop("student_login_locked_until", None)
            return 0

        if remaining_seconds <= 0:
            session.pop("student_login_locked_until", None)
            return 0

        return remaining_seconds

    def set_session_lock(remaining_seconds):
        """Store student lock expiration in session for refresh/back persistence."""
        if remaining_seconds > 0:
            session["student_login_locked_until"] = int(time.time()) + int(
                remaining_seconds
            )

    def get_ip_lock_remaining():
        """Get current lock remaining for this IP/role from login_tracker."""
        try:
            now = int(time.time())
            max_remaining = 0
            with get_db_connection().cursor() as cursor:
                cursor.execute(
                    """
                    SELECT last_attempt_at
                    FROM login_tracker
                    WHERE ip_address = %s AND user_role = %s AND is_blocked = 1
                    """,
                    (client_ip, role),
                )
                blocked_rows = cursor.fetchall() or []

            for row in blocked_rows:
                last_attempt_at = int(row.get("last_attempt_at") or 0)
                remaining = limiter.lock_duration - (now - last_attempt_at)
                if remaining > max_remaining:
                    max_remaining = remaining

            return max_remaining if max_remaining > 0 else 0
        except Exception as e:
            logger.error(f"Error reading student IP lock state: {str(e)}")
            return 0

    def lock_redirect(remaining_seconds):
        minutes = remaining_seconds // 60
        seconds = remaining_seconds % 60
        flash(
            f"Too many failed attempts. Please try again in {minutes}m {seconds}s",
            "error",
        )
        return redirect(
            url_for("auth.student_login", locked=1, seconds=remaining_seconds)
        )

    ip_remaining = get_ip_lock_remaining()

    if request.method == "POST":
        school_id = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        captcha_ok, captcha_message = _verify_turnstile_for_current_request(
            "student_login"
        )
        if not captcha_ok:
            flash(captcha_message, "error")
            return redirect(url_for("auth.student_login"))

        logger.info(
            f"Student login attempt for school ID: {school_id} from IP: {client_ip}"
        )

        # Enforce DB-backed IP lock first so refresh/cache/session changes cannot bypass lock.
        if ip_remaining > 0:
            set_session_lock(ip_remaining)
            return lock_redirect(ip_remaining)

        # Enforce persisted lock state even after refresh/navigation.
        session_remaining = get_session_lock_remaining()
        if session_remaining > 0:
            return lock_redirect(session_remaining)

        if not school_id or not password:
            logger.warning("Student login failed: Missing credentials")
            flash("Please enter both school ID and password.", "error")
            return redirect(url_for("auth.student_login"))

        # Check rate limit before processing
        allowed, message, remaining = limiter.check_rate_limit(
            school_id, client_ip, role
        )
        if not allowed:
            set_session_lock(remaining)
            flash(message, "error")
            # Redirect to login page with locked status
            return redirect(url_for("auth.student_login", locked=1, seconds=remaining))

        # Find user using raw SQL
        try:
            with get_db_connection().cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE school_id = %s", (school_id,))
                user = cursor.fetchone()
        except Exception as e:
            logger.error(f"Database error during student user lookup: {str(e)}")
            flash("An error occurred. Please try again.", "error")
            return redirect(url_for("auth.student_login"))

        if not user:
            logger.warning(f"Student login failed: User {school_id} not found")
            # Record failed attempt
            limiter.process_fail(school_id, client_ip, role)
            allowed, message, remaining = limiter.check_rate_limit(
                school_id, client_ip, role
            )
            if not allowed:
                set_session_lock(remaining)
                flash(message, "error")
                return redirect(
                    url_for("auth.student_login", locked=1, seconds=remaining)
                )
            flash("Invalid student credentials.", "error")
            return redirect(url_for("auth.student_login"))

        # Check password
        if not check_password_hash(user["password_hash"], password):
            logger.warning(
                f"Student login failed: Invalid password for user {school_id}"
            )
            # Record failed attempt
            limiter.process_fail(school_id, client_ip, role)
            allowed, message, remaining = limiter.check_rate_limit(
                school_id, client_ip, role
            )
            if not allowed:
                set_session_lock(remaining)
                flash(message, "error")
                return redirect(
                    url_for("auth.student_login", locked=1, seconds=remaining)
                )
            flash("Invalid student credentials.", "error")
            return redirect(url_for("auth.student_login"))

        # Check role
        if user["role"] != role:
            logger.warning(f"Student login failed: Role mismatch for user {school_id}")
            # Record failed attempt
            limiter.process_fail(school_id, client_ip, role)
            allowed, message, remaining = limiter.check_rate_limit(
                school_id, client_ip, role
            )
            if not allowed:
                set_session_lock(remaining)
                flash(message, "error")
                return redirect(
                    url_for("auth.student_login", locked=1, seconds=remaining)
                )
            flash("Invalid student credentials.", "error")
            return redirect(url_for("auth.student_login"))

        # Check account status
        account_status = user.get("account_status", "active")
        if account_status == "pending":
            logger.warning(
                f"Student login failed: Account pending approval for user {school_id}"
            )
            # Record failed attempt
            limiter.process_fail(school_id, client_ip, role)
            allowed, message, remaining = limiter.check_rate_limit(
                school_id, client_ip, role
            )
            if not allowed:
                set_session_lock(remaining)
                flash(message, "error")
                return redirect(
                    url_for("auth.student_login", locked=1, seconds=remaining)
                )
            flash(
                "Your account is pending approval by the administrator. You will receive an email notification once your account is approved.",
                "error",
            )
            return redirect(url_for("auth.student_login"))
        elif account_status == "rejected":
            logger.warning(
                f"Student login failed: Account rejected for user {school_id}"
            )
            # Record failed attempt
            limiter.process_fail(school_id, client_ip, role)
            allowed, message, remaining = limiter.check_rate_limit(
                school_id, client_ip, role
            )
            if not allowed:
                set_session_lock(remaining)
                flash(message, "error")
                return redirect(
                    url_for("auth.student_login", locked=1, seconds=remaining)
                )
            flash(
                "Your account registration was not approved. Please contact the administrator for more information.",
                "error",
            )
            return redirect(url_for("auth.student_login"))
        elif account_status == "suspended":
            logger.warning(
                f"Student login failed: Account suspended for user {school_id}"
            )
            # Record failed attempt
            limiter.process_fail(school_id, client_ip, role)
            allowed, message, remaining = limiter.check_rate_limit(
                school_id, client_ip, role
            )
            if not allowed:
                set_session_lock(remaining)
                flash(message, "error")
                return redirect(
                    url_for("auth.student_login", locked=1, seconds=remaining)
                )
            flash(
                "Your account has been suspended. Please contact the administrator.",
                "error",
            )
            return redirect(url_for("auth.student_login"))

        # Login successful
        session["user_id"] = user["id"]
        session["school_id"] = user["school_id"]
        session["role"] = user["role"]
        session.permanent = True

        logger.info(f"Student {school_id} logged in successfully")
        # Reset failed attempts on successful login
        limiter.process_success(school_id, client_ip, role)
        session.pop("student_login_locked_until", None)
        return redirect(url_for("dashboard.student_dashboard"))

    logger.info("Student login page accessed")
    query_locked = request.args.get("locked") == "1"
    try:
        query_seconds = int(request.args.get("seconds") or 0)
    except ValueError:
        query_seconds = 0

    session_seconds = get_session_lock_remaining()
    remaining_seconds = max(
        session_seconds,
        query_seconds if query_locked else 0,
        ip_remaining,
    )

    if remaining_seconds > 0:
        set_session_lock(remaining_seconds)

    return render_template(
        "studentlogin.html", locked=remaining_seconds > 0, seconds=remaining_seconds
    )


@auth_bp.route("/mfa-verify", methods=["GET", "POST"], endpoint="mfa_verify")
def mfa_verify():
    pending = _get_pending_mfa()
    if not pending:
        flash("No pending MFA challenge. Please log in again.", "error")
        return redirect(url_for("auth.login"))

    now = int(time.time())
    expires_at = int(pending.get("expires_at") or 0)
    remaining_seconds = max(0, expires_at - now)

    if remaining_seconds <= 0:
        session.pop("mfa_pending", None)
        flash("Your MFA code has expired. Please log in again.", "error")
        return redirect(url_for(_role_login_endpoint(pending.get("role", ""))))

    if request.method == "POST":
        action = (request.form.get("action") or "verify").strip().lower()
        remember_device_checked = (
            request.form.get("remember_device") or ""
        ).strip().lower() in {"1", "true", "yes", "on"}

        captcha_ok, captcha_message = _verify_turnstile_for_current_request(
            "mfa_verify"
        )
        if not captcha_ok:
            flash(captcha_message, "error")
            return redirect(url_for("auth.mfa_verify"))

        if action == "resend":
            last_sent_at = int(pending.get("last_sent_at") or 0)
            cooldown_left = max(0, MFA_RESEND_COOLDOWN_SECONDS - (now - last_sent_at))
            if cooldown_left > 0:
                flash(
                    f"Please wait {cooldown_left} seconds before requesting another code.",
                    "error",
                )
            else:
                code = _generate_mfa_code()
                sent = email_service.send_mfa_code_email(
                    recipient_email=pending["email"],
                    recipient_name=pending.get("school_id", "User"),
                    code=code,
                    expiry_minutes=max(1, MFA_CODE_TTL_SECONDS // 60),
                    role=pending.get("role", "user"),
                )
                if sent:
                    pending["code_hash"] = _hash_mfa_code(code)
                    pending["expires_at"] = now + MFA_CODE_TTL_SECONDS
                    pending["last_sent_at"] = now
                    session["mfa_pending"] = pending
                    flash("A new MFA code has been sent to your email.", "success")
                else:
                    flash("Unable to send a new code. Please try again.", "error")

            return redirect(url_for("auth.mfa_verify"))

        code = (request.form.get("code") or "").strip()
        if not code or not code.isdigit():
            flash("Enter the 6-digit code from your email.", "error")
            return redirect(url_for("auth.mfa_verify"))

        attempts_left = int(pending.get("attempts_left") or MFA_MAX_ATTEMPTS)
        if attempts_left <= 0:
            session.pop("mfa_pending", None)
            flash("Too many invalid MFA attempts. Please log in again.", "error")
            return redirect(url_for(_role_login_endpoint(pending.get("role", ""))))

        if not hmac.compare_digest(_hash_mfa_code(code), pending.get("code_hash", "")):
            attempts_left -= 1
            pending["attempts_left"] = attempts_left
            session["mfa_pending"] = pending
            if attempts_left <= 0:
                session.pop("mfa_pending", None)
                flash("Too many invalid MFA attempts. Please log in again.", "error")
                return redirect(url_for(_role_login_endpoint(pending.get("role", ""))))

            flash(f"Invalid code. {attempts_left} attempt(s) remaining.", "error")
            return redirect(url_for("auth.mfa_verify"))

        response = _complete_mfa_login(pending)
        if remember_device_checked:
            logger.info(f"User checked 'Remember this device' - setting trust cookie")
            try:
                _set_mfa_trust_cookie(
                    response,
                    int(pending.get("user_id") or 0),
                    str(pending.get("role") or ""),
                )
            except Exception as e:
                logger.warning(f"Failed to set MFA trust cookie: {e}")
        else:
            logger.debug("User did not check 'Remember this device'")
        return response

    return render_template(
        "mfa_verify.html",
        masked_email=_mask_email(pending.get("email", "")),
        remaining_seconds=remaining_seconds,
        role=pending.get("role"),
        attempts_left=pending.get("attempts_left"),
        resend_cooldown=MFA_RESEND_COOLDOWN_SECONDS,
        mfa_trust_enabled=MFA_TRUST_DEVICE_ENABLED,
        mfa_trust_days=MFA_TRUST_DAYS,
        remember_device_checked=True,
    )


# Route: GET "/logout"
# Used by: Logout links/buttons in various templates; session timeouts may redirect here
# Purpose: Clear session and return user to home page.
@auth_bp.route("/logout", endpoint="logout")
def logout():
    user_id = session.get("user_id")
    school_id = session.get("school_id")
    user_role = session.get("user_role", "unknown")

    # Log the logout action
    logger.info(f"User {school_id} (ID: {user_id}) logged out as {user_role}")

    # Completely clear the session
    session.clear()

    # Create response object to add headers that prevent browser caching
    response = redirect(url_for("home"))

    # Add cache-control headers to prevent back button access to authenticated pages
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response


# Route: GET/POST "/register"
# Used by: register.html (form posts here)
# Purpose: Student self-registration flow creating user, personal_info, and student profile.
@auth_bp.route("/register", methods=["GET", "POST"], endpoint="register")
def register():
    if request.method == "POST":
        logger.info("Registration form submitted")

        captcha_ok, captcha_message = _verify_turnstile_for_current_request("register")
        if not captcha_ok:
            flash(captcha_message, "error")
            return render_template("register.html")

        first_name = request.form.get("firstName", "").strip()
        last_name = request.form.get("lastName", "").strip()
        middle_name = request.form.get("middleName", "").strip() or None
        school_id = request.form.get("schoolId", "").strip()
        email = request.form.get("email", "").strip()
        course = request.form.get("course", "").strip()
        track = request.form.get("track", "").strip() or None
        year_level = request.form.get("yearLevel", "").strip()
        section = request.form.get("section", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirmPassword", "")

        # Get uploaded files
        id_front = request.files.get("idFront")
        id_back = request.files.get("idBack")
        face_photo = request.files.get("facePhoto")

        # Validation
        errors = []

        # Validate file uploads
        if not id_front or not id_front.filename:
            errors.append("ID Front photo is required")
        elif not allowed_file(id_front.filename):
            errors.append("ID Front must be a valid image file (PNG, JPG, JPEG, WEBP)")

        if not id_back or not id_back.filename:
            errors.append("ID Back photo is required")
        elif not allowed_file(id_back.filename):
            errors.append("ID Back must be a valid image file (PNG, JPG, JPEG, WEBP)")

        if not face_photo or not face_photo.filename:
            errors.append("Face photo is required")
        elif not allowed_file(face_photo.filename):
            errors.append(
                "Face photo must be a valid image file (PNG, JPG, JPEG, WEBP)"
            )

        # Check if school ID already exists
        try:
            with get_db_connection().cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM users WHERE school_id = %s", (school_id,)
                )
                existing_user = cursor.fetchone()
        except Exception as e:
            logger.error(f"Database error during registration check: {str(e)}")
            flash("An error occurred. Please try again.", "error")
            return render_template("register.html")

        if existing_user:
            errors.append("School ID already registered")
            logger.warning(f"Registration failed: School ID {school_id} already exists")

        if not first_name:
            errors.append("First name is required")
        if not last_name:
            errors.append("Last name is required")
        # School ID is required and must match format YY-NNNNN where YY is 21-26
        import re

        if not school_id:
            errors.append("School ID is required")
        elif not re.match(r"^(21|22|23|24|25|26)-\d{5}$", school_id):
            errors.append(
                "Invalid School ID format. Use YY-NNNNN (e.g., 22-12345) where YY is 21-26"
            )
        if not email:
            errors.append("Email is required")
        if not course:
            errors.append("Course is required")
        if not year_level:
            errors.append("Year level is required")
        if not section:
            errors.append("Section is required")
        if not password:
            errors.append("Password is required")
        if password != confirm_password:
            errors.append("Passwords do not match")

        # Password strength validation
        errors.extend(
            validate_password_policy(password, school_id=school_id, email=email)
        )

        if errors:
            for error in errors:
                flash(error, "error")
            logger.warning(
                f"Registration validation failed for school ID {school_id}: {errors}"
            )
            return render_template(
                "register.html",
                form_data={
                    "firstName": first_name,
                    "lastName": last_name,
                    "middleName": middle_name,
                    "schoolId": school_id,
                    "email": email,
                    "course": course,
                    "track": track,
                    "yearLevel": year_level,
                    "section": section,
                },
            )

        try:
            # Create upload directory if it doesn't exist (using absolute path)
            from pathlib import Path

            base_dir = Path(__file__).resolve().parent.parent
            upload_dir = base_dir / "static" / "uploads" / "student_photos"
            upload_dir.mkdir(parents=True, exist_ok=True)

            logger.info(f"Upload directory: {upload_dir}")

            # Save uploaded photos with secure filenames
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Save ID Front
            id_front_filename = secure_filename(
                f"{school_id}_{timestamp}_id_front.{id_front.filename.rsplit('.', 1)[1].lower()}"
            )
            id_front_path = upload_dir / id_front_filename
            id_front.save(str(id_front_path))
            id_front_relative_path = (
                f"static/uploads/student_photos/{id_front_filename}"
            )
            logger.info(f"Saved ID Front: {id_front_path}")

            # Save ID Back
            id_back_filename = secure_filename(
                f"{school_id}_{timestamp}_id_back.{id_back.filename.rsplit('.', 1)[1].lower()}"
            )
            id_back_path = upload_dir / id_back_filename
            id_back.save(str(id_back_path))
            id_back_relative_path = f"static/uploads/student_photos/{id_back_filename}"
            logger.info(f"Saved ID Back: {id_back_path}")

            # Save Face Photo
            face_photo_filename = secure_filename(
                f"{school_id}_{timestamp}_face.{face_photo.filename.rsplit('.', 1)[1].lower()}"
            )
            face_photo_path = upload_dir / face_photo_filename
            face_photo.save(str(face_photo_path))
            face_photo_relative_path = (
                f"static/uploads/student_photos/{face_photo_filename}"
            )
            logger.info(f"Saved Face Photo: {face_photo_path}")

            # Create user with pending account status
            password_hash = generate_password_hash(password)

            with get_db_connection().cursor() as cursor:
                cursor.execute(
                    "INSERT INTO users (school_id, password_hash, role, account_status) VALUES (%s, %s, %s, %s)",
                    (school_id, password_hash, "student", "pending"),
                )
                user_id = cursor.lastrowid

                # Create personal information record for student with actual names
                cursor.execute(
                    "INSERT INTO personal_info (first_name, last_name, middle_name, email) VALUES (%s, %s, %s, %s)",
                    (first_name, last_name, middle_name, email),
                )
                personal_info_id = cursor.lastrowid

                # Create student profile with pending approval status and photo paths
                cursor.execute(
                    "INSERT INTO students (user_id, personal_info_id, course, track, year_level, section, approval_status, id_front_path, id_back_path, face_photo_path) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (
                        user_id,
                        personal_info_id,
                        course,
                        track,
                        int(year_level),
                        section,
                        "pending",
                        id_front_relative_path,
                        id_back_relative_path,
                        face_photo_relative_path,
                    ),
                )

            get_db_connection().commit()

            # Send registration confirmation email
            full_name = f"{first_name} {last_name}"
            email_sent = email_service.send_registration_confirmation_email(
                student_email=email,
                student_name=full_name,
                school_id=school_id,
                course=course,
                year_level=int(year_level),
            )

            logger.info(
                f"User registration pending approval: {school_id}. Confirmation email sent: {email_sent}"
            )
            flash("registration_pending", "success")
            return redirect(url_for("auth.register"))

        except Exception as e:
            get_db_connection().rollback()
            logger.error(f"Registration failed for {school_id}: {str(e)}")
            flash("Registration failed. Please try again.", "error")
            return render_template(
                "register.html",
                form_data={
                    "schoolId": school_id,
                    "email": email,
                    "course": course,
                    "track": track,
                    "yearLevel": year_level,
                    "section": section,
                },
            )

    logger.info("Registration page accessed")
    return render_template("register.html")


# ============================================================================
# FORGOT PASSWORD ROUTES
# ============================================================================


@auth_bp.route("/forgot-password", methods=["GET", "POST"], endpoint="forgot_password")
def forgot_password():
    """Display forgot password page and handle email submission"""
    if request.method == "POST":
        captcha_ok, captcha_message = _verify_turnstile_for_current_request(
            "forgot_password"
        )
        if not captcha_ok:
            flash(captcha_message, "error")
            return render_template("forgot_password.html")

        email = request.form.get("email", "").strip().lower()
        role = request.form.get("role", "").strip().lower()

        # Get client IP for rate limiting
        client_ip = get_client_ip()

        if not email or not role:
            flash("Please provide both email and role.", "error")
            return render_template("forgot_password.html")

        if role not in ["student", "instructor"]:
            flash("Invalid role selected.", "error")
            return render_template("forgot_password.html")

        # Check rate limit before processing (use email as identifier for forgot password)
        limiter = get_login_limiter()
        allowed, message, remaining = limiter.check_rate_limit(email, client_ip)
        if not allowed:
            flash(message, "error")
            # Redirect to forgot password page with locked status
            return render_template("forgot_password.html", locked=1, seconds=remaining)

        try:
            with get_db_connection().cursor() as cursor:
                # Find user based on role
                if role == "student":
                    cursor.execute(
                        "SELECT s.id, s.user_id, pi.email, pi.first_name, pi.last_name FROM students s JOIN personal_info pi ON s.personal_info_id = pi.id WHERE pi.email = %s",
                        (email,),
                    )
                else:  # instructor
                    cursor.execute(
                        "SELECT i.id, i.user_id, pi.email, pi.first_name, pi.last_name FROM instructors i JOIN personal_info pi ON i.personal_info_id = pi.id WHERE pi.email = %s",
                        (email,),
                    )

                user = cursor.fetchone()

                # Always show success message to prevent email enumeration
                flash(
                    "If an account with that email exists, a password reset link has been sent. Please check your email.",
                    "success",
                )

                if user:
                    # Record the attempt (even successful ones for tracking)
                    limiter.process_fail(email, client_ip, f"forgot_password_{role}")
                    # Generate secure reset token
                    reset_token = secrets.token_urlsafe(32)
                    expires_at = datetime.now() + timedelta(hours=1)

                    logger.info(
                        f"Generated token for user_id {user['user_id']}: {reset_token[:10]}..."
                    )

                    # Store token in database
                    cursor.execute(
                        """INSERT INTO password_reset_tokens 
                        (user_id, token, expires_at, role) 
                        VALUES (%s, %s, %s, %s)""",
                        (user["user_id"], reset_token, expires_at, role),
                    )

                    # Commit the token to database
                    get_db_connection().commit()
                    logger.info(
                        f"Token committed to database for user_id: {user['user_id']}"
                    )

                    # Generate reset link
                    reset_link = url_for(
                        "auth.reset_password",
                        token=reset_token,
                        _external=True,
                    )

                    # Send email
                    full_name = f"{user['first_name']} {user['last_name']}"
                    email_service.send_password_reset_email(
                        recipient_email=email,
                        recipient_name=full_name,
                        reset_link=reset_link,
                        role=role.capitalize(),
                    )

                    logger.info(f"Password reset email sent to {email} ({role})")

            # Return success to show in SweetAlert before redirecting
            flash(
                "If an account with that email exists, a password reset link has been sent. Please check your email.",
                "success",
            )
            return redirect(url_for("auth.forgot_password"))

        except Exception as e:
            logger.error(f"Error in forgot password: {str(e)}")
            flash(
                "An error occurred. Please try again later or contact support.",
                "error",
            )
            return render_template("forgot_password.html")

    return render_template("forgot_password.html")


@auth_bp.route(
    "/reset-password/<token>", methods=["GET", "POST"], endpoint="reset_password"
)
def reset_password(token):
    """Handle password reset with token"""
    if request.method == "POST":
        new_password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        if not new_password or not confirm_password:
            flash("Please provide both password fields.", "error")
            return render_template("reset_password.html", token=token)

        if new_password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("reset_password.html", token=token)

        policy_errors = validate_password_policy(new_password)
        if policy_errors:
            for err in policy_errors:
                flash(err, "error")
            return render_template("reset_password.html", token=token)

        try:
            with get_db_connection().cursor() as cursor:
                # Verify token and check expiration
                cursor.execute(
                    """SELECT user_id, role, expires_at, used 
                    FROM password_reset_tokens 
                    WHERE token = %s""",
                    (token,),
                )
                token_data = cursor.fetchone()

                if not token_data:
                    flash("Invalid or expired reset link.", "error")
                    return redirect(url_for("auth.login"))

                if token_data["used"]:
                    flash("This reset link has already been used.", "error")
                    return redirect(url_for("auth.login"))

                if datetime.now() > token_data["expires_at"]:
                    flash(
                        "This reset link has expired. Please request a new one.",
                        "error",
                    )
                    return redirect(url_for("auth.forgot_password"))

                # Update password
                hashed_password = generate_password_hash(new_password)
                cursor.execute(
                    "UPDATE users SET password_hash = %s WHERE id = %s",
                    (hashed_password, token_data["user_id"]),
                )

                # Mark token as used
                cursor.execute(
                    "UPDATE password_reset_tokens SET used = 1 WHERE token = %s",
                    (token,),
                )

                # Commit the changes
                get_db_connection().commit()

                logger.info(
                    f"Password reset successful for user_id: {token_data['user_id']}"
                )

                # Render directly with success flag instead of redirecting
                flash(
                    "Your password has been reset successfully! You can now login with your new password.",
                    "success",
                )
                return render_template(
                    "reset_password.html",
                    token=token,
                    password_reset_success=True,
                    reset_role=token_data["role"],
                )

        except Exception as e:
            logger.error(f"Error resetting password: {str(e)}")
            flash("An error occurred. Please try again later.", "error")
            return render_template("reset_password.html", token=token)

    # GET request - verify token first
    try:
        with get_db_connection().cursor() as cursor:
            cursor.execute(
                """SELECT expires_at, used FROM password_reset_tokens WHERE token = %s""",
                (token,),
            )
            token_data = cursor.fetchone()

            logger.info(f"Token lookup result: {token_data} for token: {token[:10]}...")

            if not token_data:
                flash("Invalid reset link.", "error")
                logger.warning(f"Token not found in database: {token[:10]}...")
                return redirect(url_for("auth.login"))

            if token_data["used"]:
                flash("This reset link has already been used.", "error")
                return redirect(url_for("auth.login"))

            if datetime.now() > token_data["expires_at"]:
                flash("This reset link has expired. Please request a new one.", "error")
                return redirect(url_for("auth.forgot_password"))

    except Exception as e:
        logger.error(f"Error verifying token: {str(e)}")
        flash("An error occurred. Please try again later.", "error")
        return redirect(url_for("auth.login"))

    return render_template("reset_password.html", token=token)
