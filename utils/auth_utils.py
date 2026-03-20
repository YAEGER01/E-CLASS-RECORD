import logging
from functools import wraps
from flask import session, flash, redirect, url_for, request, jsonify

from utils.db_conn import get_db_connection

logger = logging.getLogger(__name__)


def login_required(f):
    """Decorator to ensure a valid session exists before accessing a route.

    Behavior matches existing app.py logic: if user_id is missing, flash and redirect to /login.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            # If this is an API request, return JSON 401 so client-side fetch can handle it
            try:
                if request and getattr(request, "path", "").startswith("/api/"):
                    return (jsonify({"error": "Authentication required"}), 401)
            except Exception:
                # Fall back to flashing/redirect for non-API contexts
                pass

            try:
                flash("Please log in to access this page.", "error")
            except Exception:
                # Flash may not be usable in some contexts; ignore
                pass
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated_function


def role_required(allowed_roles):
    """Decorator to ensure the user has one of the allowed roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session:
                # Handle unauthenticated access
                if request and getattr(request, "path", "").startswith("/api/"):
                    return jsonify({"error": "Authentication required"}), 401
                flash("Please log in to access this page.", "error")
                return redirect(url_for("auth.login"))

            user_role = session.get("role")
            if user_role not in allowed_roles:
                # Handle unauthorized access
                if request and getattr(request, "path", "").startswith("/api/"):
                    return jsonify({"error": "Access denied"}), 403
                flash("You do not have permission to access this page.", "error")
                return redirect(url_for("auth.login"))

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def log_admin_action(action, resource_type, resource_id=None, details=None):
    """Log an admin action to the audit_logs table."""
    try:
        admin_id = session.get("user_id")
        admin_school_id = session.get("school_id")

        if not admin_id or not admin_school_id:
            logger.warning("Attempted to log admin action without valid session")
            return

        ip_address = request.remote_addr if request else None
        user_agent = request.headers.get("User-Agent") if request else None

        with get_db_connection().cursor() as cursor:
            cursor.execute(
                """INSERT INTO audit_logs
                (admin_id, admin_school_id, action, resource_type, resource_id, details, ip_address, user_agent)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    admin_id,
                    admin_school_id,
                    action,
                    resource_type,
                    resource_id,
                    details,
                    ip_address,
                    user_agent,
                ),
            )

        get_db_connection().commit()
        logger.info(
            f"Admin action logged: {action} on {resource_type} by {admin_school_id}"
        )

    except Exception as e:
        logger.error(f"Failed to log admin action: {str(e)}")
        # Don't rollback here as this is logging, not the main transaction
