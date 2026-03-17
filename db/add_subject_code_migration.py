#!/usr/bin/env python3
"""
Add subject_code column to classes table
"""
import os
import sys
import pymysql
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database credentials from environment
environment = os.getenv("ENVIRONMENT", "local").lower()

if environment == "local":
    db_host = os.getenv("LOCAL_DB_HOST", "localhost")
    db_port = int(os.getenv("LOCAL_DB_PORT", "3306"))
    db_user = os.getenv("LOCAL_DB_USER", "root")
    db_password = os.getenv("LOCAL_DB_PASSWORD", "")
    db_name = os.getenv("LOCAL_DB_NAME", "e_class_record")
else:
    print("Only local environment is supported for this migration")
    sys.exit(1)

# SQL to add the column
sql_add_column = """
ALTER TABLE `classes` 
ADD COLUMN `subject_code` VARCHAR(50) NULL AFTER `subject`;
"""

try:
    # Connect to database
    print(f"Connecting to database: {db_name} at {db_host}:{db_port}")
    conn = pymysql.connect(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password,
        database=db_name,
        cursorclass=pymysql.cursors.DictCursor
    )
    
    with conn.cursor() as cursor:
        # Check if column already exists
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'classes' 
            AND COLUMN_NAME = 'subject_code'
        """, (db_name,))
        
        result = cursor.fetchone()
        
        if result['count'] > 0:
            print("Column 'subject_code' already exists in 'classes' table")
        else:
            print("Adding 'subject_code' column to 'classes' table...")
            cursor.execute(sql_add_column)
            conn.commit()
            print("✓ Column 'subject_code' added successfully!")
    
    conn.close()
    print("\nMigration completed successfully!")
    
except pymysql.Error as e:
    print(f"Database error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
