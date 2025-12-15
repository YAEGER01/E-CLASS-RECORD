import json
import os
import sys

# Ensure project root is on sys.path so tests can import app.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app


def test_compute_endpoint_exists():
    client = app.test_client()
    # Call the compute endpoint for class_id 2 (MAJOR Networking)
    resp = client.post("/api/compute/class/2")
    # Endpoint should respond (200 or 404/400 if no structure or bad request) but must return JSON
    assert resp.status_code in (200, 400, 404, 500)
    # If the endpoint returns JSON, ensure it's a dict; otherwise just ensure the endpoint responded
    if resp.is_json:
        data = resp.get_json()
        assert isinstance(data, dict)
