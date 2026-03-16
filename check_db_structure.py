"""
Check database structure to understand what columns exist
"""
from utils.db_conn import get_db_connection

try:
    conn = get_db_connection()
    with conn.cursor() as cursor:
        print("Checking personal_info table structure:")
        cursor.execute("DESCRIBE personal_info")
        for row in cursor.fetchall():
            print(row)
        
        print("\nChecking students table structure:")
        cursor.execute("DESCRIBE students")
        for row in cursor.fetchall():
            print(row)
            
        print("\nChecking users table structure:")
        cursor.execute("DESCRIBE users")
        for row in cursor.fetchall():
            print(row)
            
except Exception as e:
    print(f"Error: {e}")
