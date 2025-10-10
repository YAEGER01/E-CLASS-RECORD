#!/usr/bin/env python3
"""
Database Migration Script for E-Class Record System

This script adds personal_info_id columns to existing students and instructors tables
to link them with the existing personal_info table.

Usage:
    python migration_script.py

This script will:
1. Add personal_info_id column to students table (nullable)
2. Add personal_info_id column to instructors table (nullable)
3. Create placeholder PersonalInfo records for existing students/instructors
4. Link existing records to their PersonalInfo records

IMPORTANT: Backup your database before running this script!
"""

import os
import sys
import logging
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, User, Student, Instructor, PersonalInfo
from db_conn import init_database_with_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("migration.log")],
)
logger = logging.getLogger(__name__)


def backup_database():
    """Create a backup of the current database before migration."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"backup_before_migration_{timestamp}.sql"

        logger.info(f"Creating database backup: {backup_file}")
        # Note: This is a placeholder for actual backup logic
        # In a real scenario, you would use mysqldump or similar tool
        logger.info("⚠️  Please manually backup your database before proceeding!")
        return True
    except Exception as e:
        logger.error(f"Failed to create backup: {str(e)}")
        return False


def check_current_schema():
    """Check current database schema to understand what exists."""
    try:
        with app.app_context():
            inspector = db.inspect(db.engine)

            # Check what tables exist
            existing_tables = inspector.get_table_names()
            logger.info(f"Existing tables: {', '.join(existing_tables)}")

            # Check if personal_info table exists
            if "personal_info" in existing_tables:
                logger.info("✅ personal_info table already exists")
            else:
                logger.error("❌ personal_info table not found!")
                return False

            # Check students table columns
            if "students" in existing_tables:
                students_columns = [
                    col["name"] for col in inspector.get_columns("students")
                ]
                logger.info(f"Students table columns: {', '.join(students_columns)}")

                if "personal_info_id" in students_columns:
                    logger.info("✅ students table already has personal_info_id column")
                else:
                    logger.info("❌ students table missing personal_info_id column")

            # Check instructors table columns
            if "instructors" in existing_tables:
                instructors_columns = [
                    col["name"] for col in inspector.get_columns("instructors")
                ]
                logger.info(
                    f"Instructors table columns: {', '.join(instructors_columns)}"
                )

                if "personal_info_id" in instructors_columns:
                    logger.info(
                        "✅ instructors table already has personal_info_id column"
                    )
                else:
                    logger.info("❌ instructors table missing personal_info_id column")

            return True

    except Exception as e:
        logger.error(f"Failed to check schema: {str(e)}")
        return False


def check_existing_data():
    """Check if there's existing data in students and instructors tables."""
    try:
        with app.app_context():
            try:
                student_count = Student.query.count()
                instructor_count = Instructor.query.count()
            except Exception as e:
                if "Unknown column" in str(e):
                    # Fallback for missing columns - use basic query
                    student_count = Student.query.count()
                    instructor_count = Instructor.query.count()
                else:
                    raise e

            logger.info(f"Found {student_count} existing students")
            logger.info(f"Found {instructor_count} existing instructors")

            return student_count, instructor_count

    except Exception as e:
        logger.error(f"Failed to check existing data: {str(e)}")
        return 0, 0


def migrate_existing_data():
    """Migrate existing student and instructor data to use PersonalInfo."""
    try:
        logger.info("Starting data migration...")

        with app.app_context():
            # Get existing students
            students = Student.query.all()

            for student in students:
                try:
                    # Create PersonalInfo record for each student
                    # Since we don't have personal info for existing students,
                    # we'll create minimal records with available data
                    personal_info = PersonalInfo(
                        first_name="Unknown",
                        last_name="Student",
                        middle_name=None,
                        email=f"student.{student.id}@placeholder.edu",
                        phone=None,
                        address=None,
                        birth_date=None,
                        gender=None,
                        emergency_contact_name=None,
                        emergency_contact_phone=None,
                    )

                    db.session.add(personal_info)
                    db.session.flush()  # Get the ID

                    # Update student to reference the personal info
                    student.personal_info_id = personal_info.id
                    logger.info(f"✅ Migrated student {student.id}")

                except Exception as e:
                    logger.error(f"❌ Failed to migrate student {student.id}: {str(e)}")
                    db.session.rollback()
                    continue

            # Get existing instructors
            instructors = Instructor.query.all()

            for instructor in instructors:
                try:
                    # Create PersonalInfo record for each instructor
                    personal_info = PersonalInfo(
                        first_name="Unknown",
                        last_name="Instructor",
                        middle_name=None,
                        email=f"instructor.{instructor.id}@placeholder.edu",
                        phone=None,
                        address=None,
                        birth_date=None,
                        gender=None,
                        emergency_contact_name=None,
                        emergency_contact_phone=None,
                    )

                    db.session.add(personal_info)
                    db.session.flush()  # Get the ID

                    # Update instructor to reference the personal info
                    instructor.personal_info_id = personal_info.id
                    logger.info(f"✅ Migrated instructor {instructor.id}")

                except Exception as e:
                    logger.error(
                        f"❌ Failed to migrate instructor {instructor.id}: {str(e)}"
                    )
                    db.session.rollback()
                    continue

            # Commit all changes
            db.session.commit()
            logger.info("✅ Data migration completed successfully")

    except Exception as e:
        logger.error(f"❌ Data migration failed: {str(e)}")
        return False

    return True


def verify_migration():
    """Verify that the migration was successful."""
    try:
        logger.info("Verifying migration...")

        with app.app_context():
            # Check if PersonalInfo table exists and has data
            personal_info_count = PersonalInfo.query.count()
            logger.info(f"PersonalInfo records: {personal_info_count}")

            # Check if students have personal_info_id
            try:
                students_with_personal_info = Student.query.filter(
                    Student.personal_info_id.isnot(None)
                ).count()
                total_students = Student.query.count()
                logger.info(
                    f"Students with personal info: {students_with_personal_info}/{total_students}"
                )
            except Exception as e:
                if "Unknown column" in str(e):
                    logger.info(
                        "ℹ️  Students table doesn't have personal_info_id yet (will be added)"
                    )
                    total_students = Student.query.count()
                else:
                    logger.error(
                        f"❌ Failed to check students personal_info_id: {str(e)}"
                    )
                    return False

            # Check if instructors have personal_info_id
            try:
                instructors_with_personal_info = Instructor.query.filter(
                    Instructor.personal_info_id.isnot(None)
                ).count()
                total_instructors = Instructor.query.count()
                logger.info(
                    f"Instructors with personal info: {instructors_with_personal_info}/{total_instructors}"
                )
            except Exception as e:
                if "Unknown column" in str(e):
                    logger.info(
                        "ℹ️  Instructors table doesn't have personal_info_id yet (will be added)"
                    )
                    total_instructors = Instructor.query.count()
                else:
                    logger.error(
                        f"❌ Failed to check instructors personal_info_id: {str(e)}"
                    )
                    return False

            # Verify table structure exists (column addition was successful)
            inspector = db.inspect(db.engine)

            # Check students table has personal_info_id column
            students_columns = [
                col["name"] for col in inspector.get_columns("students")
            ]
            if "personal_info_id" not in students_columns:
                logger.error("❌ personal_info_id column not found in students table")
                return False

            # Check instructors table has personal_info_id column
            instructors_columns = [
                col["name"] for col in inspector.get_columns("instructors")
            ]
            if "personal_info_id" not in instructors_columns:
                logger.error(
                    "❌ personal_info_id column not found in instructors table"
                )
                return False

            logger.info("✅ Table structure verification successful")

            # Test foreign key relationships only if there are records
            if total_students > 0:
                sample_student = Student.query.filter(
                    Student.personal_info_id.isnot(None)
                ).first()

                if sample_student and sample_student.personal_info:
                    logger.info("✅ Foreign key relationships working correctly")
                elif students_with_personal_info == 0:
                    logger.info(
                        "ℹ️  No students have personal_info_id set (expected for new installations)"
                    )
                else:
                    logger.warning("⚠️  Foreign key relationships may have issues")
                    return False
            else:
                logger.info(
                    "ℹ️  No existing students to verify relationships (expected for new installations)"
                )

            return True

    except Exception as e:
        logger.error(f"❌ Migration verification failed: {str(e)}")
        return False


def add_personal_info_columns():
    """Add personal_info_id columns to students and instructors tables."""
    try:
        logger.info("Adding personal_info_id columns...")

        with app.app_context():
            # Add personal_info_id to students table
            try:
                with db.engine.connect() as connection:
                    # First add the column
                    connection.execute(
                        db.text(
                            "ALTER TABLE students ADD COLUMN personal_info_id INT NULL"
                        )
                    )
                    # Then add the foreign key constraint
                    connection.execute(
                        db.text(
                            "ALTER TABLE students ADD CONSTRAINT fk_students_personal_info FOREIGN KEY (personal_info_id) REFERENCES personal_info(id)"
                        )
                    )
                    connection.commit()
                logger.info("✅ Added personal_info_id to students table")
            except Exception as e:
                if "Duplicate column name" in str(e):
                    logger.info("✅ personal_info_id already exists in students table")
                else:
                    logger.error(
                        f"❌ Failed to add personal_info_id to students: {str(e)}"
                    )
                    return False

            # Add personal_info_id to instructors table
            try:
                with db.engine.connect() as connection:
                    # First add the column
                    connection.execute(
                        db.text(
                            "ALTER TABLE instructors ADD COLUMN personal_info_id INT NULL"
                        )
                    )
                    # Then add the foreign key constraint
                    connection.execute(
                        db.text(
                            "ALTER TABLE instructors ADD CONSTRAINT fk_instructors_personal_info FOREIGN KEY (personal_info_id) REFERENCES personal_info(id)"
                        )
                    )
                    connection.commit()
                logger.info("✅ Added personal_info_id to instructors table")
            except Exception as e:
                if "Duplicate column name" in str(e):
                    logger.info(
                        "✅ personal_info_id already exists in instructors table"
                    )
                else:
                    logger.error(
                        f"❌ Failed to add personal_info_id to instructors: {str(e)}"
                    )
                    return False

            # Add status and updated_at columns to instructors table for account management
            try:
                with db.engine.connect() as connection:
                    # Add status column
                    connection.execute(
                        db.text(
                            "ALTER TABLE instructors ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'active'"
                        )
                    )
                    # Add updated_at column
                    connection.execute(
                        db.text(
                            "ALTER TABLE instructors ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
                        )
                    )
                    connection.commit()
                logger.info(
                    "✅ Added status and updated_at columns to instructors table"
                )
            except Exception as e:
                if "Duplicate column name" in str(e):
                    logger.info(
                        "✅ status and updated_at columns already exist in instructors table"
                    )
                else:
                    logger.error(
                        f"❌ Failed to add status/updated_at columns to instructors: {str(e)}"
                    )
                    return False

        return True

    except Exception as e:
        logger.error(f"❌ Failed to add personal_info columns: {str(e)}")
        return False


def run_migration():
    """Run the complete migration process."""
    logger.info("🚀 Starting database migration for PersonalInfo integration...")

    # Step 1: Backup (manual step)
    if not backup_database():
        logger.error("❌ Migration aborted due to backup failure")
        return False

    # Step 2: Initialize database connection
    if not init_database_with_app(app):
        logger.error("❌ Failed to initialize database connection")
        return False

    # Step 3: Check current schema
    if not check_current_schema():
        logger.error("❌ Schema check failed")
        return False

    # Step 4: Add personal_info_id columns
    if not add_personal_info_columns():
        logger.error("❌ Failed to add personal_info_id columns")
        return False

    # Step 5: Check existing data
    student_count, instructor_count = check_existing_data()

    # Step 6: Create PersonalInfo records for existing data
    if student_count > 0 or instructor_count > 0:
        if not migrate_existing_data():
            logger.error("❌ Failed to create PersonalInfo records")
            return False

    # Step 7: Verify migration
    if not verify_migration():
        logger.error("❌ Migration verification failed")
        return False

    logger.info("🎉 Database migration completed successfully!")
    return True


if __name__ == "__main__":
    print("🗄️  E-Class Record PersonalInfo Integration Migration")
    print("=" * 60)

    # Ask for confirmation
    print("⚠️  WARNING: This will modify your database schema!")
    print(
        "This script will add personal_info_id columns to students and instructors tables."
    )
    print("Make sure you have backed up your database before proceeding.")
    print()

    confirmation = input("Do you want to continue? (yes/no): ").strip().lower()

    if confirmation in ["yes", "y"]:
        success = run_migration()
        if success:
            print("\n✅ Migration completed successfully!")
            print("You can now use the enhanced instructor creation functionality.")
        else:
            print("\n❌ Migration failed! Check the logs for details.")
            sys.exit(1)
    else:
        print("Migration cancelled.")
        sys.exit(0)
