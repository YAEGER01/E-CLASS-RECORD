import re
from app import app


def extract_csrf(html: str) -> str:
    pattern = r'<input[^>]*name=["\']csrf_token["\'][^>]*value=["\']([^"\']+)["\']'
    m = re.search(pattern, html, flags=re.IGNORECASE)
    assert m, "CSRF token not found in form"
    return m.group(1)


def test_register_post_with_csrf_returns_ok_or_200ish():
    client = app.test_client()
    # 1. GET the form
    resp = client.get("/register")
    assert resp.status_code == 200
    token = extract_csrf(resp.get_data(as_text=True))

    # 2. POST minimal valid form with CSRF token
    data = {
        "csrf_token": token,
        "schoolId": "2025-TEST-0001",
        "course": "BSIT",
        "track": "",
        "yearLevel": "1",
        "section": "A",
        "password": "Abcd12",
        "confirmPassword": "Abcd12",
    }
    resp2 = client.post("/register", data=data, follow_redirects=False)

    # We expect either a redirect to /login (302) on success or 200 with the form showing errors unrelated to CSRF
    assert resp2.status_code in (
        200,
        302,
        303,
    ), f"Unexpected status: {resp2.status_code}\nBody: {resp2.get_data(as_text=True)[:500]}"
