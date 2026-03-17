"""
Script to insert dummy students for testing grade sheet with 60 students
"""
import pymysql
from utils.db_conn import get_db_connection

def insert_dummy_students(class_id, num_students=60):
    """Insert dummy students into a class for testing"""
    inserted_user_ids = []
    inserted_student_ids = []
    inserted_personal_info_ids = []
    
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            print(f"Inserting {num_students} dummy students into class {class_id}...")
            
            for i in range(1, num_students + 1):
                # Insert personal info with required email field
                first_name = f"TestFirst{i}"
                last_name = f"TestLast{i}"
                middle_name = f"M{i}"
                email = f"test{i}@dummy.com"
                
                cursor.execute("""
                    INSERT INTO personal_info (first_name, last_name, middle_name, email)
                    VALUES (%s, %s, %s, %s)
                """, (first_name, last_name, middle_name, email))
                personal_info_id = cursor.lastrowid
                inserted_personal_info_ids.append(personal_info_id)
                
                # Insert user with password_hash (not password)
                school_id = f"99-{i:05d}"
                cursor.execute("""
                    INSERT INTO users (school_id, password_hash, role)
                    VALUES (%s, %s, %s)
                """, (school_id, 'dummy_hash', 'student'))
                user_id = cursor.lastrowid
                inserted_user_ids.append(user_id)
                
                # Insert student with required fields: course, year_level, section
                cursor.execute("""
                    INSERT INTO students (user_id, personal_info_id, course, year_level, section)
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, personal_info_id, 'BSIT', 3, '3A'))
                student_id = cursor.lastrowid
                inserted_student_ids.append(student_id)
                
                # Link student to class
                cursor.execute("""
                    INSERT INTO student_classes (student_id, class_id)
                    VALUES (%s, %s)
                """, (student_id, class_id))
                
                if i % 10 == 0:
                    print(f"Inserted {i} students...")
            
            conn.commit()
            print(f"\n✅ Successfully inserted {num_students} dummy students!")
            print(f"User IDs: {min(inserted_user_ids)} to {max(inserted_user_ids)}")
            print(f"Student IDs: {min(inserted_student_ids)} to {max(inserted_student_ids)}")
            
        return inserted_user_ids, inserted_student_ids, inserted_personal_info_ids
        
    except Exception as e:
        print(f"❌ Error inserting dummy students: {e}")
        conn.rollback()
        raise

def delete_dummy_students(user_ids, student_ids, personal_info_ids):
    """Delete the dummy students that were inserted"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            print("\nDeleting dummy students...")
            
            # Delete from student_classes
            if student_ids:
                placeholders = ','.join(['%s'] * len(student_ids))
                cursor.execute(f"DELETE FROM student_classes WHERE student_id IN ({placeholders})", student_ids)
                print(f"Deleted from student_classes")
            
            # Delete from students
            if student_ids:
                placeholders = ','.join(['%s'] * len(student_ids))
                cursor.execute(f"DELETE FROM students WHERE id IN ({placeholders})", student_ids)
                print(f"Deleted from students")
            
            # Delete from users
            if user_ids:
                placeholders = ','.join(['%s'] * len(user_ids))
                cursor.execute(f"DELETE FROM users WHERE id IN ({placeholders})", user_ids)
                print(f"Deleted from users")
            
            # Delete from personal_info
            if personal_info_ids:
                placeholders = ','.join(['%s'] * len(personal_info_ids))
                cursor.execute(f"DELETE FROM personal_info WHERE id IN ({placeholders})", personal_info_ids)
                print(f"Deleted from personal_info")
            
            conn.commit()
            print(f"\n✅ Successfully deleted all dummy students!")
            
    except Exception as e:
        print(f"❌ Error deleting dummy students: {e}")
        conn.rollback()
        raise

if __name__ == "__main__":
    # Get class_id from user
    class_id = input("Enter the class ID to test with: ")
    
    if not class_id.isdigit():
        print("Invalid class ID")
        exit(1)
    
    class_id = int(class_id)
    
    # Insert dummy students
    user_ids, student_ids, personal_info_ids = insert_dummy_students(class_id, 60)
    
    print("\n" + "="*60)
    print("Now go to the grade sheet and check if it fits on one page!")
    print("="*60)
    
    input("\nPress Enter when you're done testing to DELETE the dummy students...")
    
    # Delete dummy students
    delete_dummy_students(user_ids, student_ids, personal_info_ids)
    
    print("\nDone! All dummy students have been removed.")
