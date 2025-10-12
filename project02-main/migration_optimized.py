"""
Database Migration Script for Optimized E-Class Record System
Drops existing tables and recreates with optimized structure
"""

import os
import sys
import logging
from datetime import datetime
from flask import Flask
from db_conn import get_db_connection
from models import db

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def drop_all_tables():
    """Drop all existing tables in the correct order to handle foreign key constraints"""
    try:
        with get_db_connection().cursor() as cursor:
            # Disable foreign key checks temporarily
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

            # List of tables to drop (in reverse dependency order)
            tables_to_drop = [
                "grade_assessments",
                "class_grading_components",
                "class_grading_categories",
                "class_grading_templates",
                "grade_subcategories",
                "grade_categories",
                "grade_structures",
                "student_scores",
                "student_grades",
                "assessments",
                "grading_categories",
                "grading_templates",
                "student_classes",
                "classes",
                "instructors",
                "students",
                "personal_info",
                "users",
            ]

            # Drop each table
            for table in tables_to_drop:
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS {table}")
                    logger.info(f"✅ Dropped table: {table}")
                except Exception as e:
                    logger.warning(f"⚠️  Could not drop table {table}: {str(e)}")

            # Re-enable foreign key checks
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

        get_db_connection().commit()
        logger.info("✅ All tables dropped successfully")
        return True

    except Exception as e:
        logger.error(f"❌ Error dropping tables: {str(e)}")
        get_db_connection().rollback()
        return False


def create_all_tables():
    """Create all tables with optimized structure using PyMySQL"""
    try:
        logger.info("🔄 Creating optimized database tables using PyMySQL...")

        with get_db_connection().cursor() as cursor:
            # Create users table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    school_id VARCHAR(20) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    role VARCHAR(20) NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_users_school_id (school_id),
                    INDEX idx_users_role (role),
                    INDEX idx_users_created_at (created_at)
                )
            """
            )

            # Create personal_info table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS personal_info (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    first_name VARCHAR(50) NOT NULL,
                    last_name VARCHAR(50) NOT NULL,
                    middle_name VARCHAR(50),
                    email VARCHAR(100) NOT NULL UNIQUE,
                    phone VARCHAR(20),
                    address VARCHAR(255),
                    birth_date DATE,
                    gender VARCHAR(10),
                    emergency_contact_name VARCHAR(100),
                    emergency_contact_phone VARCHAR(20),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_personal_info_first_name (first_name),
                    INDEX idx_personal_info_last_name (last_name),
                    INDEX idx_personal_info_email (email),
                    INDEX idx_personal_info_phone (phone),
                    INDEX idx_personal_info_birth_date (birth_date),
                    INDEX idx_personal_info_gender (gender)
                )
            """
            )

            # Create students table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS students (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    personal_info_id INT,
                    course VARCHAR(10) NOT NULL,
                    track VARCHAR(50),
                    year_level INT NOT NULL,
                    section VARCHAR(10) NOT NULL,
                    id_front_path VARCHAR(255),
                    id_back_path VARCHAR(255),
                    face_photo_path VARCHAR(255),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (personal_info_id) REFERENCES personal_info(id) ON DELETE SET NULL,
                    INDEX idx_students_user_id (user_id),
                    INDEX idx_students_personal_info_id (personal_info_id),
                    INDEX idx_students_course (course),
                    INDEX idx_students_track (track),
                    INDEX idx_students_year_level (year_level),
                    INDEX idx_students_section (section)
                )
            """
            )

            # Create instructors table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS instructors (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    personal_info_id INT,
                    department VARCHAR(100),
                    specialization VARCHAR(100),
                    employee_id VARCHAR(20) UNIQUE,
                    hire_date DATE,
                    status VARCHAR(20) NOT NULL DEFAULT 'active',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (personal_info_id) REFERENCES personal_info(id) ON DELETE SET NULL,
                    INDEX idx_instructors_user_id (user_id),
                    INDEX idx_instructors_personal_info_id (personal_info_id),
                    INDEX idx_instructors_department (department),
                    INDEX idx_instructors_employee_id (employee_id),
                    INDEX idx_instructors_hire_date (hire_date),
                    INDEX idx_instructors_status (status)
                )
            """
            )

            # Create classes table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS classes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    instructor_id INT NOT NULL,
                    year VARCHAR(4) NOT NULL,
                    semester VARCHAR(20) NOT NULL,
                    course VARCHAR(10) NOT NULL,
                    track VARCHAR(50) NOT NULL,
                    section VARCHAR(10) NOT NULL,
                    schedule VARCHAR(50) NOT NULL,
                    class_code VARCHAR(36) NOT NULL UNIQUE,
                    join_code VARCHAR(6) NOT NULL UNIQUE,
                    grading_template_id INT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (instructor_id) REFERENCES instructors(id) ON DELETE CASCADE,
                    INDEX idx_classes_instructor_id (instructor_id),
                    INDEX idx_classes_year (year),
                    INDEX idx_classes_semester (semester),
                    INDEX idx_classes_course (course),
                    INDEX idx_classes_track (track),
                    INDEX idx_classes_section (section),
                    INDEX idx_classes_class_code (class_code),
                    INDEX idx_classes_join_code (join_code)
                )
            """
            )

            # Create student_classes table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS student_classes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    student_id INT NOT NULL,
                    class_id INT NOT NULL,
                    joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                    FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE,
                    UNIQUE KEY unique_student_class (student_id, class_id),
                    INDEX idx_student_classes_student_id (student_id),
                    INDEX idx_student_classes_class_id (class_id),
                    INDEX idx_student_classes_joined_at (joined_at)
                )
            """
            )

            # Create grading_templates table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS grading_templates (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    instructor_id INT NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    is_default BOOLEAN DEFAULT FALSE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (instructor_id) REFERENCES instructors(id) ON DELETE CASCADE,
                    INDEX idx_grading_templates_instructor_id (instructor_id),
                    INDEX idx_grading_templates_name (name),
                    INDEX idx_grading_templates_is_default (is_default)
                )
            """
            )

            # Create grading_categories table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS grading_categories (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    template_id INT NOT NULL,
                    name VARCHAR(50) NOT NULL,
                    weight FLOAT NOT NULL,
                    position INT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (template_id) REFERENCES grading_templates(id) ON DELETE CASCADE,
                    INDEX idx_grading_categories_template_id (template_id),
                    INDEX idx_grading_categories_name (name),
                    INDEX idx_grading_categories_position (position)
                )
            """
            )

            # Create assessments table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS assessments (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    category_id INT NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    weight FLOAT,
                    max_score FLOAT NOT NULL,
                    passing_score FLOAT,
                    position INT NOT NULL,
                    description TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES grading_categories(id) ON DELETE CASCADE,
                    INDEX idx_assessments_category_id (category_id),
                    INDEX idx_assessments_name (name),
                    INDEX idx_assessments_position (position)
                )
            """
            )

            # Create student_grades table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS student_grades (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    student_id INT NOT NULL,
                    class_id INT NOT NULL,
                    assessment_id INT NOT NULL,
                    score FLOAT,
                    percentage FLOAT,
                    letter_grade VARCHAR(2),
                    remarks VARCHAR(50),
                    graded_at DATETIME,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                    FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE,
                    FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE,
                    INDEX idx_student_grades_student_id (student_id),
                    INDEX idx_student_grades_class_id (class_id),
                    INDEX idx_student_grades_assessment_id (assessment_id),
                    INDEX idx_student_grades_letter_grade (letter_grade),
                    INDEX idx_student_grades_graded_at (graded_at)
                )
            """
            )

            # Create student_scores table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS student_scores (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    assessment_id INT NOT NULL,
                    student_id INT NOT NULL,
                    score FLOAT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE,
                    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                    INDEX idx_student_scores_assessment_id (assessment_id),
                    INDEX idx_student_scores_student_id (student_id)
                )
            """
            )

            # Create grade_structures table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS grade_structures (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    class_id INT NOT NULL,
                    structure_name VARCHAR(100) NOT NULL,
                    structure_json TEXT NOT NULL,
                    created_by INT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE,
                    FOREIGN KEY (created_by) REFERENCES instructors(id) ON DELETE CASCADE,
                    INDEX idx_grade_structures_class_id (class_id),
                    INDEX idx_grade_structures_structure_name (structure_name),
                    INDEX idx_grade_structures_created_by (created_by),
                    INDEX idx_grade_structures_is_active (is_active)
                )
            """
            )

            # Create grade_categories table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS grade_categories (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    structure_id INT NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    weight FLOAT NOT NULL,
                    position INT NOT NULL,
                    description TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (structure_id) REFERENCES grade_structures(id) ON DELETE CASCADE,
                    INDEX idx_grade_categories_structure_id (structure_id),
                    INDEX idx_grade_categories_name (name),
                    INDEX idx_grade_categories_position (position)
                )
            """
            )

            # Create grade_subcategories table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS grade_subcategories (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    category_id INT NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    weight FLOAT,
                    max_score FLOAT NOT NULL,
                    passing_score FLOAT,
                    position INT NOT NULL,
                    description TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES grade_categories(id) ON DELETE CASCADE,
                    INDEX idx_grade_subcategories_category_id (category_id),
                    INDEX idx_grade_subcategories_name (name),
                    INDEX idx_grade_subcategories_position (position)
                )
            """
            )

            # Create grade_assessments table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS grade_assessments (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    subcategory_id INT NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    weight FLOAT,
                    max_score FLOAT NOT NULL,
                    passing_score FLOAT,
                    position INT NOT NULL,
                    description TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (subcategory_id) REFERENCES grade_subcategories(id) ON DELETE CASCADE,
                    INDEX idx_grade_assessments_subcategory_id (subcategory_id),
                    INDEX idx_grade_assessments_name (name),
                    INDEX idx_grade_assessments_position (position)
                )
            """
            )

            # Create class_grading_templates table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS class_grading_templates (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    class_id INT NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE,
                    INDEX idx_class_grading_templates_class_id (class_id),
                    INDEX idx_class_grading_templates_name (name),
                    INDEX idx_class_grading_templates_is_active (is_active)
                )
            """
            )

            # Create class_grading_categories table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS class_grading_categories (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    template_id INT NOT NULL,
                    name VARCHAR(50) NOT NULL,
                    weight FLOAT NOT NULL,
                    position INT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (template_id) REFERENCES class_grading_templates(id) ON DELETE CASCADE,
                    INDEX idx_class_grading_categories_template_id (template_id),
                    INDEX idx_class_grading_categories_name (name),
                    INDEX idx_class_grading_categories_position (position)
                )
            """
            )

            # Create class_grading_components table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS class_grading_components (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    category_id INT NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    max_score FLOAT NOT NULL,
                    weight FLOAT,
                    position INT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES class_grading_categories(id) ON DELETE CASCADE,
                    INDEX idx_class_grading_components_category_id (category_id),
                    INDEX idx_class_grading_components_name (name),
                    INDEX idx_class_grading_components_position (position)
                )
            """
            )

        get_db_connection().commit()
        logger.info("✅ All optimized tables created successfully using PyMySQL")
        return True

    except Exception as e:
        logger.error(f"❌ Error creating tables: {str(e)}")
        get_db_connection().rollback()
        return False


def verify_table_structure():
    """Verify that all tables were created with correct structure"""
    try:
        with get_db_connection().cursor() as cursor:
            # Check key tables
            key_tables = [
                "users",
                "personal_info",
                "students",
                "instructors",
                "classes",
            ]

            for table in key_tables:
                cursor.execute(f"DESCRIBE {table}")
                columns = cursor.fetchall()
                logger.info(f"✅ Table {table}: {len(columns)} columns")

                # Show key columns for verification
                for col in columns[:5]:  # Show first 5 columns
                    logger.info(
                        f"   - {col['Field']}: {col['Type']} ({'NULL' if col['Null'] == 'YES' else 'NOT NULL'})"
                    )

        return True

    except Exception as e:
        logger.error(f"❌ Error verifying table structure: {str(e)}")
        return False


def main():
    """Main migration function"""
    logger.info("🚀 Starting Optimized Database Migration...")
    logger.info(f"Started at: {datetime.now()}")

    # Step 1: Drop existing tables
    logger.info("📋 Step 1: Dropping existing tables...")
    if not drop_all_tables():
        logger.error("❌ Migration failed during table drop")
        sys.exit(1)

    # Step 2: Create optimized tables
    logger.info("📋 Step 2: Creating optimized tables...")
    if not create_all_tables():
        logger.error("❌ Migration failed during table creation")
        sys.exit(1)

    # Step 3: Verify structure
    logger.info("📋 Step 3: Verifying table structure...")
    if not verify_table_structure():
        logger.error("❌ Migration failed during verification")
        sys.exit(1)

    logger.info("🎉 Migration completed successfully!")
    logger.info(f"Completed at: {datetime.now()}")
    logger.info(
        "✅ Your database now has optimized, fast, and secure table structures!"
    )

    return True


if __name__ == "__main__":
    main()
