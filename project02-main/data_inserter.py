#!/usr/bin/env python3
"""
Advanced Data Inserter for E-Class Record System
Features:
- Relationship-aware data insertion
- Random and targeted data generation
- Bulk operations
- Delete functionality
- Conflict resolution
"""

import os
import sys
import random
import string
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime, date
import uuid
import hashlib

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, Student, Instructor, Class, StudentClass, generate_class_codes
from db_conn import init_database_with_app

# Initialize database
try:
    init_database_with_app(app)
except Exception as e:
    print(f"Database initialization warning: {e}")

# Data generators
class DataGenerator:
    """Generate random data for different tables"""

    @staticmethod
    def generate_school_id(role='student', existing_ids=None):
        """Generate unique school ID"""
        if existing_ids is None:
            existing_ids = []

        prefix = {
            'student': '23',
            'instructor': 'INS',
            'admin': 'ADM'
        }.get(role, '23')

        while True:
            if role == 'student':
                number = f"{random.randint(10000, 99999)}"
                school_id = f"{prefix}-{number}"
            elif role == 'instructor':
                number = f"{random.randint(1000, 9999)}"
                school_id = f"{prefix}{number}"
            else:  # admin
                number = f"{random.randint(100, 999)}"
                school_id = f"{prefix}{number}"

            if school_id not in existing_ids:
                return school_id

    @staticmethod
    def generate_password():
        """Generate secure password"""
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(random.choice(chars) for _ in range(10))

    @staticmethod
    def generate_course():
        """Generate random course"""
        courses = ['BSIT', 'BSCS', 'BSIS', 'BSECE', 'BSCE']
        return random.choice(courses)

    @staticmethod
    def generate_track(course):
        """Generate track based on course"""
        tracks = {
            'BSIT': ['Programming', 'Networking', 'Web Development', 'Database Management'],
            'BSCS': ['Software Engineering', 'Data Science', 'AI/ML', 'Cybersecurity'],
            'BSIS': ['System Analysis', 'Database Admin', 'IT Management'],
            'BSECE': ['Embedded Systems', 'Communications', 'Electronics'],
            'BSCE': ['Civil Engineering', 'Structural Design', 'Construction Management']
        }
        return random.choice(tracks.get(course, ['General']))

    @staticmethod
    def generate_department():
        """Generate random department"""
        departments = ['Computer Science', 'Information Technology', 'Engineering',
                      'Mathematics', 'Business Administration', 'Education']
        return random.choice(departments)

    @staticmethod
    def generate_schedule():
        """Generate random class schedule"""
        days = ['M-W-F', 'T-Th', 'M-T-W-Th-F', 'Sat', 'Sun']
        times = ['8-10AM', '10-12PM', '1-3PM', '3-5PM', '6-8PM']
        return f"{random.choice(days)} {random.choice(times)}"

class DataInserterApp:
    """Main application class"""

    def __init__(self, root):
        self.root = root
        self.root.title("E-Class Record - Advanced Data Inserter")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)

        # Initialize data storage
        self.existing_data = {
            'users': [],
            'students': [],
            'instructors': [],
            'classes': [],
            'student_classes': []
        }

        # Status bar (create before loading data)
        self.status_var = tk.StringVar()
        self.status_var.set("Initializing...")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill='x', side='bottom')

        self.load_existing_data()

        # Create notebook (tabs)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Create tabs
        self.create_insert_tab()
        self.create_delete_tab()
        self.create_modify_tab()
        self.create_view_tab()

        # Status bar already created above

    def load_existing_data(self):
        """Load existing data to avoid conflicts"""
        with app.app_context():
            try:
                self.existing_data['users'] = [u.school_id for u in User.query.all()]
                self.existing_data['students'] = [s.user.school_id for s in Student.query.all()]
                self.existing_data['instructors'] = [i.user.school_id for i in Instructor.query.all()]
                self.existing_data['classes'] = [c.class_code for c in Class.query.all()]
                self.status_var.set("Existing data loaded successfully")
            except Exception as e:
                self.status_var.set(f"Error loading existing data: {str(e)}")

    def create_insert_tab(self):
        """Create the insert data tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Insert Data")

        # Table selection
        table_frame = ttk.LabelFrame(frame, text="Table Selection")
        table_frame.pack(fill='x', padx=10, pady=5)

        self.table_var = tk.StringVar(value='users')
        tables = ['users', 'students', 'instructors', 'classes', 'student_classes']
        for table in tables:
            ttk.Radiobutton(table_frame, text=table.title(),
                           variable=self.table_var, value=table).pack(side='left', padx=10)

        # Options frame
        options_frame = ttk.LabelFrame(frame, text="Options")
        options_frame.pack(fill='x', padx=10, pady=5)

        # Quantity selection
        ttk.Label(options_frame, text="Quantity:").grid(row=0, column=0, padx=5, pady=5)
        self.quantity_var = tk.IntVar(value=1)
        ttk.Spinbox(options_frame, from_=1, to=100, textvariable=self.quantity_var).grid(row=0, column=1, padx=5, pady=5)

        # Data type selection
        ttk.Label(options_frame, text="Data Type:").grid(row=0, column=2, padx=5, pady=5)
        self.data_type_var = tk.StringVar(value='random')
        ttk.Radiobutton(options_frame, text="Random", variable=self.data_type_var, value='random').grid(row=0, column=3, padx=5)
        ttk.Radiobutton(options_frame, text="Targeted", variable=self.data_type_var, value='targeted').grid(row=0, column=4, padx=5)

        # Role selection (for users)
        ttk.Label(options_frame, text="Role:").grid(row=1, column=0, padx=5, pady=5)
        self.role_var = tk.StringVar(value='student')
        role_combo = ttk.Combobox(options_frame, textvariable=self.role_var,
                                 values=['student', 'instructor', 'admin'])
        role_combo.grid(row=1, column=1, padx=5, pady=5)
        role_combo.state(['readonly'])

        # Insert button
        ttk.Button(options_frame, text="Insert Data", command=self.insert_data).grid(row=2, column=0, columnspan=5, pady=10)

        # Progress and results
        self.insert_progress = ttk.Progressbar(frame, mode='determinate')
        self.insert_progress.pack(fill='x', padx=10, pady=5)

        self.insert_results = scrolledtext.ScrolledText(frame, height=15)
        self.insert_results.pack(fill='both', expand=True, padx=10, pady=5)

    def create_delete_tab(self):
        """Create the delete data tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Delete Data")

        # Delete options
        options_frame = ttk.LabelFrame(frame, text="Delete Options")
        options_frame.pack(fill='x', padx=10, pady=5)

        # Delete type
        self.delete_type_var = tk.StringVar(value='individual')
        ttk.Radiobutton(options_frame, text="Individual Records",
                       variable=self.delete_type_var, value='individual').pack(side='left', padx=10)
        ttk.Radiobutton(options_frame, text="Bulk Delete",
                       variable=self.delete_type_var, value='bulk').pack(side='left', padx=10)

        # Table selection for bulk delete
        bulk_frame = ttk.LabelFrame(frame, text="Bulk Delete Options")
        bulk_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(bulk_frame, text="Table:").grid(row=0, column=0, padx=5, pady=5)
        self.bulk_table_var = tk.StringVar(value='users')
        bulk_combo = ttk.Combobox(bulk_frame, textvariable=self.bulk_table_var,
                                 values=['users', 'students', 'instructors', 'classes', 'student_classes'])
        bulk_combo.grid(row=0, column=1, padx=5, pady=5)
        bulk_combo.state(['readonly'])

        ttk.Label(bulk_frame, text="Condition:").grid(row=1, column=0, padx=5, pady=5)
        self.bulk_condition_var = tk.StringVar(value='all')
        condition_combo = ttk.Combobox(bulk_frame, textvariable=self.bulk_condition_var,
                                      values=['all', 'older_than', 'by_role', 'by_course'])
        condition_combo.grid(row=1, column=1, padx=5, pady=5)
        condition_combo.state(['readonly'])

        # Individual delete
        individual_frame = ttk.LabelFrame(frame, text="Individual Delete")
        individual_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(individual_frame, text="Record ID:").grid(row=0, column=0, padx=5, pady=5)
        self.delete_id_var = tk.StringVar()
        ttk.Entry(individual_frame, textvariable=self.delete_id_var).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(individual_frame, text="Table:").grid(row=1, column=0, padx=5, pady=5)
        self.individual_table_var = tk.StringVar(value='users')
        individual_combo = ttk.Combobox(individual_frame, textvariable=self.individual_table_var,
                                       values=['users', 'students', 'instructors', 'classes', 'student_classes'])
        individual_combo.grid(row=1, column=1, padx=5, pady=5)
        individual_combo.state(['readonly'])

        # Delete buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill='x', padx=10, pady=5)

        ttk.Button(button_frame, text="Delete Selected", command=self.delete_individual).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Bulk Delete", command=self.delete_bulk).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Refresh Data", command=self.load_existing_data).pack(side='right', padx=5)

        # Results
        self.delete_results = scrolledtext.ScrolledText(frame, height=15)
        self.delete_results.pack(fill='both', expand=True, padx=10, pady=5)

    def create_modify_tab(self):
        """Create the modify data tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Modify Data")

        # Modify options
        options_frame = ttk.LabelFrame(frame, text="Modify Options")
        options_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(options_frame, text="Table:").grid(row=0, column=0, padx=5, pady=5)
        self.modify_table_var = tk.StringVar(value='users')
        modify_combo = ttk.Combobox(options_frame, textvariable=self.modify_table_var,
                                   values=['users', 'students', 'instructors', 'classes'])
        modify_combo.grid(row=0, column=1, padx=5, pady=5)
        modify_combo.state(['readonly'])

        ttk.Label(options_frame, text="Record ID:").grid(row=1, column=0, padx=5, pady=5)
        self.modify_id_var = tk.StringVar()
        ttk.Entry(options_frame, textvariable=self.modify_id_var).grid(row=1, column=1, padx=5, pady=5)

        # Modify fields will be dynamically created
        self.modify_fields_frame = ttk.LabelFrame(frame, text="Fields to Modify")
        self.modify_fields_frame.pack(fill='both', expand=True, padx=10, pady=5)

        ttk.Button(options_frame, text="Load Record", command=self.load_record_for_modify).grid(row=2, column=0, columnspan=2, pady=10)

        # Results
        self.modify_results = scrolledtext.ScrolledText(frame, height=10)
        self.modify_results.pack(fill='both', expand=True, padx=10, pady=5)

    def create_view_tab(self):
        """Create the view data tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="View Data")

        # View options
        options_frame = ttk.LabelFrame(frame, text="View Options")
        options_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(options_frame, text="Table:").grid(row=0, column=0, padx=5, pady=5)
        self.view_table_var = tk.StringVar(value='users')
        view_combo = ttk.Combobox(options_frame, textvariable=self.view_table_var,
                                 values=['users', 'students', 'instructors', 'classes', 'student_classes'])
        view_combo.grid(row=0, column=1, padx=5, pady=5)
        view_combo.state(['readonly'])

        ttk.Button(options_frame, text="View Data", command=self.view_data).grid(row=0, column=2, padx=10)

        # Results
        self.view_results = scrolledtext.ScrolledText(frame, height=20)
        self.view_results.pack(fill='both', expand=True, padx=10, pady=5)

    def insert_data(self):
        """Insert data based on selections"""
        table = self.table_var.get()
        quantity = self.quantity_var.get()
        data_type = self.data_type_var.get()
        role = self.role_var.get()

        self.insert_results.delete(1.0, tk.END)
        self.insert_progress['value'] = 0
        self.status_var.set(f"Inserting {quantity} records into {table}...")

        success_count = 0
        errors = []

        with app.app_context():
            for i in range(quantity):
                try:
                    if table == 'users':
                        self.insert_user(role, data_type)
                    elif table == 'students':
                        self.insert_student(data_type)
                    elif table == 'instructors':
                        self.insert_instructor(data_type)
                    elif table == 'classes':
                        self.insert_class(data_type)
                    elif table == 'student_classes':
                        self.insert_student_class(data_type)

                    success_count += 1
                    self.insert_progress['value'] = (i + 1) / quantity * 100
                    self.root.update_idletasks()

                except Exception as e:
                    errors.append(f"Record {i+1}: {str(e)}")

        # Update results
        result_text = f"✅ Successfully inserted {success_count} records into {table}\n\n"
        if errors:
            result_text += f"❌ {len(errors)} errors occurred:\n"
            for error in errors[:5]:  # Show first 5 errors
                result_text += f"• {error}\n"
            if len(errors) > 5:
                result_text += f"... and {len(errors) - 5} more errors\n"

        self.insert_results.insert(tk.END, result_text)
        self.status_var.set(f"Insertion complete: {success_count} success, {len(errors)} errors")

        # Refresh existing data
        self.load_existing_data()

    def insert_user(self, role, data_type):
        """Insert a user record"""
        school_id = DataGenerator.generate_school_id(role, self.existing_data['users'])
        password = DataGenerator.generate_password()

        user = User(school_id=school_id, role=role)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        self.existing_data['users'].append(school_id)
        self.insert_results.insert(tk.END, f"✓ Created user: {school_id} (role: {role})\n")

    def insert_student(self, data_type):
        """Insert a student record"""
        # Find available users without student profiles
        with app.app_context():
            available_users = User.query.filter_by(role='student').filter(
                ~User.id.in_([s.user_id for s in Student.query.all()])
            ).all()

        if not available_users:
            raise ValueError("No available users for student profiles")

        user = random.choice(available_users)
        course = DataGenerator.generate_course()
        track = DataGenerator.generate_track(course)

        student = Student(
            user_id=user.id,
            course=course,
            track=track,
            year_level=random.randint(1, 4),
            section=f"{random.randint(1, 4)}{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}"
        )

        db.session.add(student)
        db.session.commit()

        self.existing_data['students'].append(user.school_id)
        self.insert_results.insert(tk.END, f"✓ Created student profile for: {user.school_id} ({course})\n")

    def insert_instructor(self, data_type):
        """Insert an instructor record"""
        # Find available users without instructor profiles
        with app.app_context():
            available_users = User.query.filter_by(role='instructor').filter(
                ~User.id.in_([i.user_id for i in Instructor.query.all()])
            ).all()

        if not available_users:
            raise ValueError("No available users for instructor profiles")

        user = random.choice(available_users)
        department = DataGenerator.generate_department()

        instructor = Instructor(
            user_id=user.id,
            department=department,
            specialization=f"{department} Specialist",
            employee_id=f"EMP{random.randint(1000, 9999)}"
        )

        db.session.add(instructor)
        db.session.commit()

        self.existing_data['instructors'].append(user.school_id)
        self.insert_results.insert(tk.END, f"✓ Created instructor profile for: {user.school_id} ({department})\n")

    def insert_class(self, data_type):
        """Insert a class record"""
        # Find available instructors
        with app.app_context():
            instructors = Instructor.query.all()

        if not instructors:
            raise ValueError("No instructors available for class creation")

        instructor = random.choice(instructors)
        course = DataGenerator.generate_course()
        track = DataGenerator.generate_track(course)
        year = str(random.randint(2024, 2026))
        semester = random.choice(['1st sem', '2nd sem'])

        class_code, join_code = generate_class_codes()

        # Ensure unique codes
        while Class.query.filter_by(class_code=class_code).first():
            class_code, join_code = generate_class_codes()
        while Class.query.filter_by(join_code=join_code).first():
            class_code, join_code = generate_class_codes()

        class_obj = Class(
            instructor_id=instructor.id,
            year=year,
            semester=semester,
            course=course,
            track=track,
            section=f"{random.randint(1, 4)}{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}",
            schedule=DataGenerator.generate_schedule(),
            class_code=class_code,
            join_code=join_code
        )

        db.session.add(class_obj)
        db.session.commit()

        self.existing_data['classes'].append(class_code)
        self.insert_results.insert(tk.END, f"✓ Created class: {class_obj.class_id} (Instructor: {instructor.user.school_id})\n")

    def insert_student_class(self, data_type):
        """Insert a student-class enrollment"""
        # Find available students and classes
        with app.app_context():
            students = Student.query.all()
            classes = Class.query.all()

        if not students or not classes:
            raise ValueError("No students or classes available for enrollment")

        student = random.choice(students)
        class_obj = random.choice(classes)

        # Check if already enrolled
        existing = StudentClass.query.filter_by(
            student_id=student.id,
            class_id=class_obj.id
        ).first()

        if existing:
            raise ValueError(f"Student {student.user.school_id} already enrolled in {class_obj.class_id}")

        enrollment = StudentClass(
            student_id=student.id,
            class_id=class_obj.id
        )

        db.session.add(enrollment)
        db.session.commit()

        self.insert_results.insert(tk.END, f"✓ Enrolled {student.user.school_id} in {class_obj.class_id}\n")

    def delete_individual(self):
        """Delete individual record"""
        table = self.individual_table_var.get()
        record_id = self.delete_id_var.get().strip()

        if not record_id:
            messagebox.showerror("Error", "Please enter a record ID")
            return

        try:
            with app.app_context():
                if table == 'users':
                    record = User.query.get(int(record_id))
                    if record:
                        db.session.delete(record)
                        db.session.commit()
                        self.delete_results.insert(tk.END, f"✓ Deleted user: {record.school_id}\n")
                    else:
                        self.delete_results.insert(tk.END, f"❌ User with ID {record_id} not found\n")

                elif table == 'students':
                    record = Student.query.get(int(record_id))
                    if record:
                        db.session.delete(record)
                        db.session.commit()
                        self.delete_results.insert(tk.END, f"✓ Deleted student profile: {record.user.school_id}\n")
                    else:
                        self.delete_results.insert(tk.END, f"❌ Student with ID {record_id} not found\n")

                elif table == 'instructors':
                    record = Instructor.query.get(int(record_id))
                    if record:
                        db.session.delete(record)
                        db.session.commit()
                        self.delete_results.insert(tk.END, f"✓ Deleted instructor profile: {record.user.school_id}\n")
                    else:
                        self.delete_results.insert(tk.END, f"❌ Instructor with ID {record_id} not found\n")

                elif table == 'classes':
                    record = Class.query.get(int(record_id))
                    if record:
                        db.session.delete(record)
                        db.session.commit()
                        self.delete_results.insert(tk.END, f"✓ Deleted class: {record.class_id}\n")
                    else:
                        self.delete_results.insert(tk.END, f"❌ Class with ID {record_id} not found\n")

                elif table == 'student_classes':
                    record = StudentClass.query.get(int(record_id))
                    if record:
                        db.session.delete(record)
                        db.session.commit()
                        self.delete_results.insert(tk.END, f"✓ Deleted enrollment: Student {record.student_id} from Class {record.class_id}\n")
                    else:
                        self.delete_results.insert(tk.END, f"❌ Enrollment with ID {record_id} not found\n")

            self.load_existing_data()
            self.status_var.set(f"Individual record deleted from {table}")

        except Exception as e:
            self.delete_results.insert(tk.END, f"❌ Error deleting record: {str(e)}\n")

    def delete_bulk(self):
        """Perform bulk delete operation"""
        table = self.bulk_table_var.get()
        condition = self.bulk_condition_var.get()

        if not messagebox.askyesno("Confirm Bulk Delete",
                                  f"Are you sure you want to delete records from {table} with condition '{condition}'?"):
            return

        try:
            with app.app_context():
                deleted_count = 0

                if table == 'users':
                    if condition == 'all':
                        deleted_count = User.query.delete()
                    elif condition == 'by_role':
                        # This would need additional UI for role selection
                        pass

                elif table == 'students':
                    if condition == 'all':
                        deleted_count = Student.query.delete()

                elif table == 'instructors':
                    if condition == 'all':
                        deleted_count = Instructor.query.delete()

                elif table == 'classes':
                    if condition == 'all':
                        deleted_count = Class.query.delete()

                elif table == 'student_classes':
                    if condition == 'all':
                        deleted_count = StudentClass.query.delete()

                db.session.commit()
                self.delete_results.insert(tk.END, f"✓ Bulk deleted {deleted_count} records from {table}\n")
                self.status_var.set(f"Bulk delete completed: {deleted_count} records deleted")

            self.load_existing_data()

        except Exception as e:
            self.delete_results.insert(tk.END, f"❌ Error in bulk delete: {str(e)}\n")

    def load_record_for_modify(self):
        """Load record for modification"""
        table = self.modify_table_var.get()
        record_id = self.modify_id_var.get().strip()

        if not record_id:
            messagebox.showerror("Error", "Please enter a record ID")
            return

        # Clear previous fields
        for widget in self.modify_fields_frame.winfo_children():
            widget.destroy()

        try:
            with app.app_context():
                if table == 'users':
                    record = User.query.get(int(record_id))
                    if record:
                        self.create_modify_fields_users(record)
                elif table == 'students':
                    record = Student.query.get(int(record_id))
                    if record:
                        self.create_modify_fields_students(record)
                elif table == 'instructors':
                    record = Instructor.query.get(int(record_id))
                    if record:
                        self.create_modify_fields_instructors(record)
                elif table == 'classes':
                    record = Class.query.get(int(record_id))
                    if record:
                        self.create_modify_fields_classes(record)

        except Exception as e:
            messagebox.showerror("Error", f"Error loading record: {str(e)}")

    def create_modify_fields_users(self, user):
        """Create modification fields for users"""
        ttk.Label(self.modify_fields_frame, text="School ID:").grid(row=0, column=0, padx=5, pady=5)
        school_id_var = tk.StringVar(value=user.school_id)
        ttk.Entry(self.modify_fields_frame, textvariable=school_id_var).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self.modify_fields_frame, text="Role:").grid(row=1, column=0, padx=5, pady=5)
        role_var = tk.StringVar(value=user.role)
        role_combo = ttk.Combobox(self.modify_fields_frame, textvariable=role_var,
                                 values=['student', 'instructor', 'admin'])
        role_combo.grid(row=1, column=1, padx=5, pady=5)
        role_combo.state(['readonly'])

        def save_changes():
            try:
                with app.app_context():
                    user.school_id = school_id_var.get()
                    user.role = role_var.get()
                    db.session.commit()
                    self.modify_results.insert(tk.END, f"✓ Updated user {user.id}\n")
            except Exception as e:
                self.modify_results.insert(tk.END, f"❌ Error updating user: {str(e)}\n")

        ttk.Button(self.modify_fields_frame, text="Save Changes", command=save_changes).grid(row=2, column=0, columnspan=2, pady=10)

    def create_modify_fields_students(self, student):
        """Create modification fields for students"""
        ttk.Label(self.modify_fields_frame, text="Course:").grid(row=0, column=0, padx=5, pady=5)
        course_var = tk.StringVar(value=student.course)
        ttk.Entry(self.modify_fields_frame, textvariable=course_var).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self.modify_fields_frame, text="Year Level:").grid(row=1, column=0, padx=5, pady=5)
        year_var = tk.IntVar(value=student.year_level)
        ttk.Spinbox(self.modify_fields_frame, from_=1, to=4, textvariable=year_var).grid(row=1, column=1, padx=5, pady=5)

        def save_changes():
            try:
                with app.app_context():
                    student.course = course_var.get()
                    student.year_level = year_var.get()
                    db.session.commit()
                    self.modify_results.insert(tk.END, f"✓ Updated student {student.id}\n")
            except Exception as e:
                self.modify_results.insert(tk.END, f"❌ Error updating student: {str(e)}\n")

        ttk.Button(self.modify_fields_frame, text="Save Changes", command=save_changes).grid(row=2, column=0, columnspan=2, pady=10)

    def create_modify_fields_instructors(self, instructor):
        """Create modification fields for instructors"""
        ttk.Label(self.modify_fields_frame, text="Department:").grid(row=0, column=0, padx=5, pady=5)
        dept_var = tk.StringVar(value=instructor.department or "")
        ttk.Entry(self.modify_fields_frame, textvariable=dept_var).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self.modify_fields_frame, text="Specialization:").grid(row=1, column=0, padx=5, pady=5)
        spec_var = tk.StringVar(value=instructor.specialization or "")
        ttk.Entry(self.modify_fields_frame, textvariable=spec_var).grid(row=1, column=1, padx=5, pady=5)

        def save_changes():
            try:
                with app.app_context():
                    instructor.department = dept_var.get()
                    instructor.specialization = spec_var.get()
                    db.session.commit()
                    self.modify_results.insert(tk.END, f"✓ Updated instructor {instructor.id}\n")
            except Exception as e:
                self.modify_results.insert(tk.END, f"❌ Error updating instructor: {str(e)}\n")

        ttk.Button(self.modify_fields_frame, text="Save Changes", command=save_changes).grid(row=2, column=0, columnspan=2, pady=10)

    def create_modify_fields_classes(self, class_obj):
        """Create modification fields for classes"""
        ttk.Label(self.modify_fields_frame, text="Course:").grid(row=0, column=0, padx=5, pady=5)
        course_var = tk.StringVar(value=class_obj.course)
        ttk.Entry(self.modify_fields_frame, textvariable=course_var).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self.modify_fields_frame, text="Schedule:").grid(row=1, column=0, padx=5, pady=5)
        schedule_var = tk.StringVar(value=class_obj.schedule)
        ttk.Entry(self.modify_fields_frame, textvariable=schedule_var).grid(row=1, column=1, padx=5, pady=5)

        def save_changes():
            try:
                with app.app_context():
                    class_obj.course = course_var.get()
                    class_obj.schedule = schedule_var.get()
                    db.session.commit()
                    self.modify_results.insert(tk.END, f"✓ Updated class {class_obj.id}\n")
            except Exception as e:
                self.modify_results.insert(tk.END, f"❌ Error updating class: {str(e)}\n")

        ttk.Button(self.modify_fields_frame, text="Save Changes", command=save_changes).grid(row=2, column=0, columnspan=2, pady=10)

    def view_data(self):
        """View data from selected table"""
        table = self.view_table_var.get()

        self.view_results.delete(1.0, tk.END)
        self.status_var.set(f"Loading data from {table}...")

        try:
            with app.app_context():
                if table == 'users':
                    records = User.query.all()
                    for user in records:
                        self.view_results.insert(tk.END, f"ID: {user.id}, School ID: {user.school_id}, Role: {user.role}\n")

                elif table == 'students':
                    records = Student.query.all()
                    for student in records:
                        self.view_results.insert(tk.END, f"ID: {student.id}, User: {student.user.school_id}, Course: {student.course}, Year: {student.year_level}\n")

                elif table == 'instructors':
                    records = Instructor.query.all()
                    for instructor in records:
                        self.view_results.insert(tk.END, f"ID: {instructor.id}, User: {instructor.user.school_id}, Department: {instructor.department}\n")

                elif table == 'classes':
                    records = Class.query.all()
                    for class_obj in records:
                        self.view_results.insert(tk.END, f"ID: {class_obj.id}, Class ID: {class_obj.class_id}, Instructor: {class_obj.instructor.user.school_id}\n")

                elif table == 'student_classes':
                    records = StudentClass.query.all()
                    for enrollment in records:
                        self.view_results.insert(tk.END, f"ID: {enrollment.id}, Student: {enrollment.student.user.school_id}, Class: {enrollment.class_obj.class_id}\n")

            self.status_var.set(f"Loaded {len(records)} records from {table}")

        except Exception as e:
            self.view_results.insert(tk.END, f"❌ Error loading data: {str(e)}\n")
            self.status_var.set(f"Error loading data from {table}")


def main():
    root = tk.Tk()
    app = DataInserterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()