"""
Script to find class ID based on class details
"""
from utils.db_conn import get_db_connection

def find_class_id():
    """Find class ID for IT 311 BSIT 3A-NS"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Search for the class
            cursor.execute("""
                SELECT c.id, c.subject_code, c.subject, c.course, c.section, 
                       CONCAT(pi.first_name, ' ', pi.last_name) as instructor_name
                FROM classes c
                LEFT JOIN instructors i ON c.instructor_id = i.id
                LEFT JOIN personal_info pi ON i.personal_info_id = pi.id
                WHERE c.subject_code = 'IT 311' OR c.subject LIKE '%DATABASE%'
                ORDER BY c.id DESC
            """)
            
            results = cursor.fetchall()
            
            if results:
                print("\nFound classes:")
                print("-" * 100)
                print(f"{'ID':<5} {'Subject Code':<15} {'Subject':<35} {'Course':<10} {'Section':<10} {'Instructor':<20}")
                print("-" * 100)
                
                for row in results:
                    class_id = row[0] if isinstance(row, tuple) else row.get('id')
                    subject_code = row[1] if isinstance(row, tuple) else row.get('subject_code')
                    subject = row[2] if isinstance(row, tuple) else row.get('subject')
                    course = row[3] if isinstance(row, tuple) else row.get('course')
                    section = row[4] if isinstance(row, tuple) else row.get('section')
                    instructor = row[5] if isinstance(row, tuple) else row.get('instructor_name')
                    
                    print(f"{class_id:<5} {subject_code or 'N/A':<15} {subject or 'N/A':<35} {course or 'N/A':<10} {section or 'N/A':<10} {instructor or 'N/A':<20}")
                
                print("-" * 100)
                print(f"\nFound {len(results)} class(es)")
            else:
                print("No classes found matching the criteria")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_class_id()
