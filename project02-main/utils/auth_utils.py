import logging
from functools import wraps
from flask import session, flash, redirect, url_for

logger = logging.getLogger(__name__)


def login_required(f):
    """Decorator to ensure a valid session exists before accessing a route.

    Behavior matches existing app.py logic: if user_id is missing, flash and redirect to /login.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            try:
                flash("Please log in to access this page.", "error")
            except Exception:
                # Flash may not be usable in some contexts; ignore
                pass
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated_function
