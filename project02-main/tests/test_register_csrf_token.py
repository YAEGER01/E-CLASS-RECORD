import re

# Import the Flask app instance
from app import app


def test_register_get_includes_csrf_token():
    client = app.test_client()
    resp = client.get("/register")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    # Check that a hidden input named csrf_token is present
    assert 'name="csrf_token"' in html, "CSRF token input not found in /register form"
    # Optionally ensure that a token value is present (non-empty)
    # This is a simple heuristic to see a value attribute next to csrf input
    pattern = r'<input[^>]*name=["\']csrf_token["\'][^>]*value=["\']([^"\']+)["\']'
    match = re.search(pattern, html, flags=re.IGNORECASE)
    assert match and match.group(1), "CSRF token value not rendered"
