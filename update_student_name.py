"""
Script to update student name in the database
"""
from utils.db_conn import get_db_connection

def update_student_name(school_id, first_name, last_name, middle_name):
    try:
        with get_db_connection().cursor() as cursor:
            # First, find the user and their personal_info_id
            cursor.execute("""
                SELECT u.id, s.personal_info_id 
                FROM users u
                JOIN students s ON u.id = s.user_id
                WHERE u.school_id = %s
            """, (school_id,))
            
            result = cursor.fetchone()
            if not result:
                print(f"Student with school ID {school_id} not found!")
                return False
            
            user_id = result['id']
            personal_info_id = result['personal_info_id']
            
            print(f"Found student: user_id={user_id}, personal_info_id={personal_info_id}")
            
            # Update the personal_info table
            cursor.execute("""
                UPDATE personal_info 
                SET first_name = %s, last_name = %s, middle_name = %s
                WHERE id = %s
            """, (first_name, last_name, middle_name, personal_info_id))
            
            get_db_connection().commit()
            print(f"Successfully updated name for {school_id} to: {last_name}, {first_name} {middle_name}")
            return True
            
    except Exception as e:
        print(f"Error updating student name: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Update the student with school_id 23-15472
    update_student_name("23-15472", "JASMINE", "ROTUGAL", "L")
