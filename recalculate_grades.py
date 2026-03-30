#!/usr/bin/env python3
"""
Script to clear released grades so they can be recalculated with new ISU thresholds
Run this before instructors re-release grades
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

import mysql.connector

def get_connection():
    """Get database connection from environment variables"""
    return mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )

def clear_released_grades():
    """Clear all released grades to force recalculation with new thresholds"""
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        print("=" * 60)
        print("GRADE RECALCULATION UTILITY")
        print("=" * 60)
        print("\nThis will clear all released grades to recalculate with new ISU thresholds:")
        print("  Old: 97.5(1.0), 94.5(1.25), 91.5(1.5), etc.")
        print("  New: 98(1.0), 95(1.25), 92(1.5), etc.")
        print("\nInstructors will need to re-release grades for them to be recalculated.\n")
        
        # Get count of released grades
        cursor.execute("SELECT COUNT(*) as count FROM released_grades WHERE status = 'released'")
        result = cursor.fetchone()
        released_count = result[0] if result else 0
        
        if released_count == 0:
            print("✓ No released grades to clear. System is ready!")
            cursor.close()
            conn.close()
            return True
        
        print(f"Found {released_count} released grade(s) to clear.\n")
        
        # Ask for confirmation
        response = input("Proceed with clearing released grades? (yes/no): ").strip().lower()
        
        if response not in ['yes', 'y']:
            print("\nOperation cancelled.")
            cursor.close()
            conn.close()
            return False
        
        # Clear released grades by setting status to 'pending'
        delete_query = "DELETE FROM released_grades WHERE status = 'released'"
        cursor.execute(delete_query)
        conn.commit()
        
        affected_rows = cursor.rowcount
        
        print(f"\n✓ Successfully cleared {affected_rows} released grade(s).")
        print("\nNext steps:")
        print("1. Instructors should go to Release Grades page")
        print("2. Re-release grades - they'll be calculated with new ISU thresholds")
        print("3. Students will see updated equivalent grades (1.0-5.0 scale)")
        print("\nISU Grading Scale (Applied):")
        print("  98-100  → 1.0 (Excellent)")
        print("  95-97   → 1.25")
        print("  92-94   → 1.5")
        print("  89-91   → 1.75")
        print("  86-88   → 2.0")
        print("  83-85   → 2.25")
        print("  80-82   → 2.5")
        print("  77-79   → 2.75")
        print("  75-76   → 3.0")
        print("  <75     → 5.0 (Failing)")
        print("=" * 60)
        
        cursor.close()
        conn.close()
        return True
        
    except mysql.connector.Error as err:
        print(f"❌ Database error: {err}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = clear_released_grades()
    sys.exit(0 if success else 1)
