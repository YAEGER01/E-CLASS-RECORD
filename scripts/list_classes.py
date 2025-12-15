"""List classes and join codes using the app's DB helper.
Run from the repo root (Windows PowerShell):

    python .\scripts\list_classes.py

This uses the same DB configuration as the app (env vars / hardcoded defaults).
"""

import sys
import traceback

# Ensure we can import utils from parent directory
sys.path.insert(0, ".")

try:
    from utils.db_conn import get_db_connection
except Exception as e:
    print(
        "Failed to import get_db_connection from utils. Make sure you're running from the repo root."
    )
    traceback.print_exc()
    sys.exit(1)

try:
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, class_code, join_code, course, section FROM classes ORDER BY id DESC LIMIT 200"
        )
        rows = cur.fetchall()
        if not rows:
            print("No classes found in the database (empty result set).")
        else:
            print(f"Found {len(rows)} classes (showing up to 200):\n")
            for r in rows:
                print(r)
    try:
        conn.close()
    except Exception:
        pass
except Exception as e:
    print("Database query failed:")
    traceback.print_exc()
    sys.exit(2)

print("\nDone.")
