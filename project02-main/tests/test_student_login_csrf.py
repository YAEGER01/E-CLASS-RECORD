import re
from app import app


def extract_csrf(html: str) -> str:
    pattern = r'<input[^>]*name=["\']csrf_token["\'][^>]*value=["\']([^"\']+)["\']'
    m = re.search(pattern, html, flags=re.IGNORECASE)
    assert m, "CSRF token not found in form"
    return m.group(1)


def test_student_login_get_includes_csrf():
    client = app.test_client()
    resp = client.get("/student-login")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert 'name="csrf_token"' in html


def test_student_login_post_with_csrf_200_or_redirect():
    client = app.test_client()
    r = client.get("/student-login")
    token = extract_csrf(r.get_data(as_text=True))
    data = {
        "csrf_token": token,
        "username": "dummy",
        "password": "dummy",
        "role": "student",
    }
    r2 = client.post("/student-login", data=data, follow_redirects=False)
    # Expect either redirect to dashboard on real creds or 200 with error flash (but not 400 CSRF)
    assert r2.status_code in (200, 302, 303)
