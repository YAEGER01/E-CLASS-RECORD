"""
Check if the student approval system database columns exist
Run this script to verify if the database migration has been applied
"""

import sys
from utils.db_conn import get_db_connection

def check_database_schema():
    """Check if required columns exist in the database"""
    print("=" * 60)
    print("Student Approval System - Database Schema Check")
    print("=" * 60)
    print()
    
    try:
        with get_db_connection().cursor() as cursor:
            # Check students table columns
            print("Checking 'students' table columns...")
            cursor.execute("DESCRIBE students")
            students_columns = [row['Field'] for row in cursor.fetchall()]
            
            required_students_columns = [
                'approval_status',
                'approved_by',
                'approved_at',
                'rejection_reason'
            ]
            
            students_missing = []
            for col in required_students_columns:
                if col in students_columns:
                    print(f"  ✓ Column '{col}' exists")
                else:
                    print(f"  ✗ Column '{col}' MISSING")
                    students_missing.append(col)
            
            print()
            
            # Check users table columns
            print("Checking 'users' table columns...")
            cursor.execute("DESCRIBE users")
            users_columns = [row['Field'] for row in cursor.fetchall()]
            
            required_users_columns = ['account_status']
            
            users_missing = []
            for col in required_users_columns:
                if col in users_columns:
                    print(f"  ✓ Column '{col}' exists")
                else:
                    print(f"  ✗ Column '{col}' MISSING")
                    users_missing.append(col)
            
            print()
            print("=" * 60)
            
            if students_missing or users_missing:
                print("❌ DATABASE MIGRATION REQUIRED")
                print("=" * 60)
                print()
                print("Missing columns detected. You need to run the SQL migration.")
                print()
                print("To fix this issue:")
                print("1. Connect to your database:")
                print("   mysql -u your_username -p your_database")
                print()
                print("2. Run the migration file:")
                print("   source db/add_student_approval_status.sql")
                print()
                print("Or copy and paste the SQL commands from:")
                print("   db/add_student_approval_status.sql")
                print()
                return False
            else:
                print("✅ ALL REQUIRED COLUMNS EXIST")
                print("=" * 60)
                print()
                print("Database schema is correct!")
                print("The student approval system should work properly.")
                print()
                
                # Check if there are any pending registrations
                cursor.execute(
                    "SELECT COUNT(*) as count FROM students WHERE approval_status = 'pending'"
                )
                pending_count = cursor.fetchone()['count']
                
                print(f"Pending registrations: {pending_count}")
                
                if pending_count > 0:
                    print(f"✓ Found {pending_count} pending student registration(s)")
                else:
                    print("No pending registrations at this time")
                
                print()
                return True
                
    except Exception as e:
        print("❌ ERROR")
        print("=" * 60)
        print(f"Error checking database schema: {str(e)}")
        print()
        print("Common issues:")
        print("1. Database connection problem")
        print("2. Wrong database credentials")
        print("3. Database server not running")
        print()
        return False

if __name__ == "__main__":
    success = check_database_schema()
    sys.exit(0 if success else 1)
