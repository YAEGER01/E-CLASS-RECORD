"""
Optimized Database Models for E-Class Record System
Fast, Secure, and Well-Structured with Proper Relationships
"""

import uuid
import hashlib
import random
import string
import json
from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    """Core user account model with optimized structure"""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    school_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(
        db.String(20), nullable=False, index=True
    )  # student, instructor, admin
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp(), index=True)

    # Optimized relationships with proper cascade handling
    student_profile = db.relationship(
        "Student",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    instructor_profile = db.relationship(
        "Instructor",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def set_password(self, password):
        """Secure password hashing"""
        self.password_hash = generate_password_hash(
            password, method="pbkdf2:sha256", salt_length=16
        )

    def check_password(self, password):
        """Secure password verification"""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "school_id": self.school_id,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<User {self.school_id} ({self.role})>"


class PersonalInfo(db.Model):
    """Personal information model - optimized for performance"""

    __tablename__ = "personal_info"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(50), nullable=False, index=True)
    last_name = db.Column(db.String(50), nullable=False, index=True)
    middle_name = db.Column(db.String(50), nullable=True, index=True)
    email = db.Column(db.String(100), nullable=False, unique=True, index=True)
    phone = db.Column(db.String(20), nullable=True, index=True)
    address = db.Column(db.String(255), nullable=True)
    birth_date = db.Column(db.Date, nullable=True, index=True)
    gender = db.Column(db.String(10), nullable=True, index=True)
    emergency_contact_name = db.Column(db.String(100), nullable=True)
    emergency_contact_phone = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp(), index=True)
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
        index=True,
    )

    # Optimized relationships with proper back_populates
    student_profile = db.relationship(
        "Student",
        back_populates="personal_info",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    instructor_profile = db.relationship(
        "Instructor",
        back_populates="personal_info",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @property
    def full_name(self):
        """Return full name with middle name if available"""
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "middle_name": self.middle_name,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "birth_date": self.birth_date.isoformat() if self.birth_date else None,
            "gender": self.gender,
            "emergency_contact_name": self.emergency_contact_name,
            "emergency_contact_phone": self.emergency_contact_phone,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<PersonalInfo {self.full_name} ({self.email})>"


class Student(db.Model):
    """Student profile model - optimized with proper relationships"""

    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    personal_info_id = db.Column(
        db.Integer, db.ForeignKey("personal_info.id"), nullable=True, index=True
    )
    course = db.Column(db.String(10), nullable=False, index=True)  # BSIT, BSCS, etc.
    track = db.Column(
        db.String(50), nullable=True, index=True
    )  # Programming, Networking, etc.
    year_level = db.Column(db.Integer, nullable=False, index=True)  # 1, 2, 3, 4
    section = db.Column(db.String(10), nullable=False, index=True)
    id_front_path = db.Column(db.String(255), nullable=True)
    id_back_path = db.Column(db.String(255), nullable=True)
    face_photo_path = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp(), index=True)

    # Optimized relationships
    user = db.relationship("User", back_populates="student_profile")
    personal_info = db.relationship("PersonalInfo", back_populates="student_profile")
    enrollments = db.relationship(
        "StudentClass", back_populates="student", cascade="all, delete-orphan"
    )
    grades = db.relationship(
        "StudentGrade", back_populates="student", cascade="all, delete-orphan"
    )
    scores = db.relationship(
        "StudentScore", back_populates="student", cascade="all, delete-orphan"
    )

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "personal_info_id": self.personal_info_id,
            "course": self.course,
            "track": self.track,
            "year_level": self.year_level,
            "section": self.section,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "student_name": (
                self.personal_info.full_name
                if self.personal_info
                else f"Student {self.id}"
            ),
            "school_id": self.user.school_id if self.user else "Unknown",
        }

    def __repr__(self):
        return f"<Student {self.user.school_id if self.user else self.id} - {self.course} {self.section}>"


class Instructor(db.Model):
    __tablename__ = "instructors"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    personal_info_id = db.Column(
        db.Integer, db.ForeignKey("personal_info.id"), nullable=True
    )
    department = db.Column(db.String(100), nullable=True)
    specialization = db.Column(db.String(100), nullable=True)
    employee_id = db.Column(db.String(20), nullable=True)
    hire_date = db.Column(db.Date, nullable=True)
    status = db.Column(
        db.String(20), nullable=False, default="active"
    )  # active, suspended
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )

    # Relationships
    classes = db.relationship(
        "Class", backref="instructor", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Instructor {self.user.school_id} - {self.department} ({self.status})>"

    @property
    def is_active(self):
        """Check if instructor account is active"""
        return self.status == "active"

    @property
    def display_status(self):
        """Return formatted status for display"""
        return self.status.title() if self.status else "Unknown"

    @property
    def full_name(self):
        """Get full name from personal info"""
        if self.personal_info:
            return self.personal_info.full_name
        return f"Instructor {self.id}"


def generate_class_codes():
    """Generate unique 36-character class code and 6-digit join code"""
    # Generate 36-character encrypted code using UUID
    class_code = str(uuid.uuid4())

    # Generate 6-digit join code from hash of the class_code
    hash_obj = hashlib.md5(class_code.encode())
    hash_hex = hash_obj.hexdigest()
    # Take first 6 characters and convert to digits only
    join_code = "".join(c for c in hash_hex[:6] if c.isdigit())
    # If not enough digits, pad with random digits
    while len(join_code) < 6:
        join_code += str(random.randint(0, 9))

    return class_code, join_code[:6]  # Ensure exactly 6 digits


class Class(db.Model):
    __tablename__ = "classes"

    id = db.Column(db.Integer, primary_key=True)
    instructor_id = db.Column(
        db.Integer, db.ForeignKey("instructors.id"), nullable=False
    )
    year = db.Column(db.String(4), nullable=False)  # e.g., "2024", "2025"
    semester = db.Column(db.String(20), nullable=False)  # e.g., "1st sem", "2nd sem"
    course = db.Column(db.String(10), nullable=False)  # e.g., "BSIT", "BSCS"
    track = db.Column(
        db.String(50), nullable=False
    )  # e.g., "Programming", "Networking"
    section = db.Column(db.String(10), nullable=False)  # e.g., "1A", "2B"
    schedule = db.Column(db.String(50), nullable=False)  # e.g., "M-W-F 8-10AM"
    class_code = db.Column(
        db.String(36), unique=True, nullable=False
    )  # 36-char encrypted unique code
    join_code = db.Column(
        db.String(6), unique=True, nullable=False
    )  # 6-digit code for students
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )

    def __repr__(self):
        return f"<Class {self.year}-{self.semester} {self.course} {self.section}>"

    @property
    def class_id(self):
        """Generate formatted class ID like '24-1 BSIT 1A'"""
        formatted_year = self.year[-2:]  # Last 2 digits of year
        formatted_semester = (
            "1"
            if "1st" in self.semester.lower()
            else "2" if "2nd" in self.semester.lower() else self.semester
        )
        return f"{formatted_year}-{formatted_semester} {self.course} {self.section}"


class StudentClass(db.Model):
    """Model for student-class enrollments (many-to-many relationship)"""

    __tablename__ = "student_classes"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id"), nullable=False)
    joined_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relationships
    student = db.relationship("Student", backref="enrollments")
    class_obj = db.relationship("Class", backref="enrollments")

    # Constraints
    __table_args__ = (
        db.UniqueConstraint("student_id", "class_id", name="unique_student_class"),
    )

    def __repr__(self):
        return f"<StudentClass student:{self.student_id} class:{self.class_id}>"


class GradingTemplate(db.Model):
    __tablename__ = "grading_templates"

    id = db.Column(db.Integer, primary_key=True)
    instructor_id = db.Column(
        db.Integer, db.ForeignKey("instructors.id"), nullable=False
    )
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )

    # Relationships
    categories = db.relationship(
        "GradingCategory", backref="template", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<GradingTemplate {self.name}>"


class GradingCategory(db.Model):
    __tablename__ = "grading_categories"

    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(
        db.Integer, db.ForeignKey("grading_templates.id"), nullable=False
    )
    name = db.Column(db.String(50), nullable=False)
    weight = db.Column(db.Float, nullable=False)
    position = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relationships
    assessments = db.relationship(
        "Assessment", backref="category", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<GradingCategory {self.name} ({self.weight}%)>"


class Instructor(db.Model):
    """Instructor profile model - optimized with proper relationships"""

    __tablename__ = "instructors"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    personal_info_id = db.Column(
        db.Integer, db.ForeignKey("personal_info.id"), nullable=True, index=True
    )
    department = db.Column(db.String(100), nullable=True, index=True)
    specialization = db.Column(db.String(100), nullable=True)
    employee_id = db.Column(db.String(20), nullable=True, unique=True, index=True)
    hire_date = db.Column(db.Date, nullable=True, index=True)
    status = db.Column(db.String(20), nullable=False, default="active", index=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp(), index=True)
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
        index=True,
    )

    # Optimized relationships
    user = db.relationship("User", back_populates="instructor_profile")
    personal_info = db.relationship("PersonalInfo", back_populates="instructor_profile")
    classes = db.relationship(
        "Class", back_populates="instructor", cascade="all, delete-orphan"
    )
    grading_templates = db.relationship(
        "GradingTemplate", back_populates="instructor", cascade="all, delete-orphan"
    )

    @property
    def is_active(self):
        """Check if instructor account is active"""
        return self.status == "active"

    @property
    def display_status(self):
        """Return formatted status for display"""
        return self.status.title() if self.status else "Unknown"

    @property
    def full_name(self):
        """Get full name from personal info"""
        if self.personal_info:
            return self.personal_info.full_name
        return f"Instructor {self.id}"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "personal_info_id": self.personal_info_id,
            "department": self.department,
            "specialization": self.specialization,
            "employee_id": self.employee_id,
            "hire_date": self.hire_date.isoformat() if self.hire_date else None,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "instructor_name": self.full_name,
            "school_id": self.user.school_id if self.user else "Unknown",
        }

    def __repr__(self):
        return f"<Instructor {self.user.school_id if self.user else self.id} - {self.department} ({self.status})>"


class Class(db.Model):
    """Class model - optimized with proper relationships and computed properties"""

    __tablename__ = "classes"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    instructor_id = db.Column(
        db.Integer, db.ForeignKey("instructors.id"), nullable=False, index=True
    )
    year = db.Column(db.String(4), nullable=False, index=True)  # e.g., "2024", "2025"
    semester = db.Column(
        db.String(20), nullable=False, index=True
    )  # e.g., "1st sem", "2nd sem"
    course = db.Column(
        db.String(10), nullable=False, index=True
    )  # e.g., "BSIT", "BSCS"
    track = db.Column(
        db.String(50), nullable=False, index=True
    )  # e.g., "Programming", "Networking"
    section = db.Column(db.String(10), nullable=False, index=True)  # e.g., "1A", "2B"
    schedule = db.Column(db.String(50), nullable=False)  # e.g., "M-W-F 8-10AM"
    class_code = db.Column(
        db.String(36), unique=True, nullable=False, index=True
    )  # 36-char encrypted unique code
    join_code = db.Column(
        db.String(6), unique=True, nullable=False, index=True
    )  # 6-digit code for students
    grading_template_id = db.Column(db.Integer, nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp(), index=True)
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
        index=True,
    )

    # Optimized relationships
    instructor = db.relationship("Instructor", back_populates="classes")
    enrollments = db.relationship(
        "StudentClass", back_populates="class_obj", cascade="all, delete-orphan"
    )
    grade_structures = db.relationship(
        "GradeStructure", back_populates="class_obj", cascade="all, delete-orphan"
    )

    @property
    def class_id(self):
        """Generate formatted class ID like '24-1 BSIT 1A'"""
        formatted_year = self.year[-2:]  # Last 2 digits of year
        formatted_semester = (
            "1"
            if "1st" in self.semester.lower()
            else "2" if "2nd" in self.semester.lower() else self.semester
        )
        return f"{formatted_year}-{formatted_semester} {self.course} {self.section}"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "instructor_id": self.instructor_id,
            "year": self.year,
            "semester": self.semester,
            "course": self.course,
            "track": self.track,
            "section": self.section,
            "schedule": self.schedule,
            "class_id": self.class_id,
            "class_code": self.class_code,
            "join_code": self.join_code,
            "grading_template_id": self.grading_template_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<Class {self.class_id}>"


class StudentClass(db.Model):
    """Student-class enrollments (many-to-many relationship) - optimized"""

    __tablename__ = "student_classes"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(
        db.Integer, db.ForeignKey("students.id"), nullable=False, index=True
    )
    class_id = db.Column(
        db.Integer, db.ForeignKey("classes.id"), nullable=False, index=True
    )
    joined_at = db.Column(db.DateTime, default=db.func.current_timestamp(), index=True)

    # Optimized relationships
    student = db.relationship("Student", back_populates="enrollments")
    class_obj = db.relationship("Class", back_populates="enrollments")

    # Constraints for data integrity
    __table_args__ = (
        db.UniqueConstraint("student_id", "class_id", name="unique_student_class"),
        db.Index("idx_student_class_joined", "student_id", "class_id"),
    )

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "student_id": self.student_id,
            "class_id": self.class_id,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
        }

    def __repr__(self):
        return f"<StudentClass student:{self.student_id} class:{self.class_id}>"


# Advanced Grading System Models
class GradingTemplate(db.Model):
    """Grading template model - optimized for complex grading structures"""

    __tablename__ = "grading_templates"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    instructor_id = db.Column(
        db.Integer, db.ForeignKey("instructors.id"), nullable=False, index=True
    )
    name = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    is_default = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp(), index=True)
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
        index=True,
    )

    # Optimized relationships
    instructor = db.relationship("Instructor", back_populates="grading_templates")
    categories = db.relationship(
        "GradingCategory", back_populates="template", cascade="all, delete-orphan"
    )

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "instructor_id": self.instructor_id,
            "name": self.name,
            "description": self.description,
            "is_default": self.is_default,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<GradingTemplate {self.name}>"


class GradingCategory(db.Model):
    """Grading category model - optimized for hierarchical grading"""

    __tablename__ = "grading_categories"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    template_id = db.Column(
        db.Integer, db.ForeignKey("grading_templates.id"), nullable=False, index=True
    )
    name = db.Column(db.String(50), nullable=False, index=True)
    weight = db.Column(db.Float, nullable=False)
    position = db.Column(db.Integer, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp(), index=True)

    # Optimized relationships
    template = db.relationship("GradingTemplate", back_populates="categories")
    assessments = db.relationship(
        "Assessment", back_populates="category", cascade="all, delete-orphan"
    )

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "template_id": self.template_id,
            "name": self.name,
            "weight": self.weight,
            "position": self.position,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<GradingCategory {self.name} ({self.weight}%)>"


class Assessment(db.Model):
    """Assessment model - optimized for various assessment types"""

    __tablename__ = "assessments"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category_id = db.Column(
        db.Integer, db.ForeignKey("grading_categories.id"), nullable=False, index=True
    )
    name = db.Column(db.String(100), nullable=False, index=True)
    weight = db.Column(db.Float, nullable=True)
    max_score = db.Column(db.Float, nullable=False)
    passing_score = db.Column(db.Float, nullable=True)
    position = db.Column(db.Integer, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp(), index=True)

    # Optimized relationships
    category = db.relationship("GradingCategory", back_populates="assessments")
    student_scores = db.relationship(
        "StudentScore", back_populates="assessment", cascade="all, delete-orphan"
    )

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "category_id": self.category_id,
            "name": self.name,
            "weight": self.weight,
            "max_score": self.max_score,
            "passing_score": self.passing_score,
            "position": self.position,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Assessment {self.name} ({self.max_score} pts)>"


class StudentGrade(db.Model):
    """Student grades model - optimized for grade tracking"""

    __tablename__ = "student_grades"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(
        db.Integer, db.ForeignKey("students.id"), nullable=False, index=True
    )
    class_id = db.Column(
        db.Integer, db.ForeignKey("classes.id"), nullable=False, index=True
    )
    assessment_id = db.Column(
        db.Integer, db.ForeignKey("assessments.id"), nullable=False, index=True
    )
    score = db.Column(db.Float, nullable=True)
    percentage = db.Column(db.Float, nullable=True)
    letter_grade = db.Column(db.String(2), nullable=True, index=True)
    remarks = db.Column(db.String(50), nullable=True)
    graded_at = db.Column(db.DateTime, nullable=True, index=True)
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
        index=True,
    )

    # Optimized relationships
    student = db.relationship("Student", back_populates="grades")
    class_obj = db.relationship("Class")
    assessment = db.relationship("Assessment")

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "student_id": self.student_id,
            "class_id": self.class_id,
            "assessment_id": self.assessment_id,
            "score": self.score,
            "percentage": self.percentage,
            "letter_grade": self.letter_grade,
            "remarks": self.remarks,
            "graded_at": self.graded_at.isoformat() if self.graded_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<StudentGrade student:{self.student_id} assessment:{self.assessment_id} score:{self.score}>"


class StudentScore(db.Model):
    """Student scores model - optimized for detailed score tracking"""

    __tablename__ = "student_scores"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    assessment_id = db.Column(
        db.Integer, db.ForeignKey("assessments.id"), nullable=False, index=True
    )
    student_id = db.Column(
        db.Integer, db.ForeignKey("students.id"), nullable=False, index=True
    )
    score = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp(), index=True)
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
        index=True,
    )

    # Optimized relationships
    assessment = db.relationship("Assessment", back_populates="student_scores")
    student = db.relationship("Student", back_populates="scores")

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "assessment_id": self.assessment_id,
            "student_id": self.student_id,
            "score": self.score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<StudentScore student:{self.student_id} assessment:{self.assessment_id} score:{self.score}>"


# Advanced Grade Structure Models
class GradeStructure(db.Model):
    """Grade structure model - optimized for complex grading hierarchies"""

    __tablename__ = "grade_structures"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    class_id = db.Column(
        db.Integer, db.ForeignKey("classes.id"), nullable=False, index=True
    )
    structure_name = db.Column(db.String(100), nullable=False, index=True)
    structure_json = db.Column(db.Text, nullable=False)  # JSON structure definition
    created_by = db.Column(
        db.Integer, db.ForeignKey("instructors.id"), nullable=False, index=True
    )
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp(), index=True)
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
        index=True,
    )
    is_active = db.Column(db.Boolean, default=True, index=True)

    # Optimized relationships
    class_obj = db.relationship("Class", back_populates="grade_structures")
    creator = db.relationship("Instructor")
    categories = db.relationship(
        "GradeCategory", back_populates="structure", cascade="all, delete-orphan"
    )

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "class_id": self.class_id,
            "structure_name": self.structure_name,
            "structure_json": self.structure_json,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_active": self.is_active,
        }

    def __repr__(self):
        return f"<GradeStructure {self.structure_name}>"


class GradeCategory(db.Model):
    """Grade category model - optimized for hierarchical grade organization"""

    __tablename__ = "grade_categories"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    structure_id = db.Column(
        db.Integer, db.ForeignKey("grade_structures.id"), nullable=False, index=True
    )
    name = db.Column(db.String(100), nullable=False, index=True)
    weight = db.Column(db.Float, nullable=False)
    position = db.Column(db.Integer, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp(), index=True)

    # Optimized relationships
    structure = db.relationship("GradeStructure", back_populates="categories")
    subcategories = db.relationship(
        "GradeSubcategory", back_populates="category", cascade="all, delete-orphan"
    )

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "structure_id": self.structure_id,
            "name": self.name,
            "weight": self.weight,
            "position": self.position,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<GradeCategory {self.name} ({self.weight}%)>"


class GradeSubcategory(db.Model):
    """Grade subcategory model - optimized for detailed grade breakdown"""

    __tablename__ = "grade_subcategories"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category_id = db.Column(
        db.Integer, db.ForeignKey("grade_categories.id"), nullable=False, index=True
    )
    name = db.Column(db.String(100), nullable=False, index=True)
    weight = db.Column(db.Float, nullable=True)
    max_score = db.Column(db.Float, nullable=False)
    passing_score = db.Column(db.Float, nullable=True)
    position = db.Column(db.Integer, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp(), index=True)

    # Optimized relationships
    category = db.relationship("GradeCategory", back_populates="subcategories")

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "category_id": self.category_id,
            "name": self.name,
            "weight": self.weight,
            "max_score": self.max_score,
            "passing_score": self.passing_score,
            "position": self.position,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<GradeSubcategory {self.name} ({self.max_score} pts)>"


class GradeAssessment(db.Model):
    """Grade assessment model - optimized for assessment-grade relationships"""

    __tablename__ = "grade_assessments"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    subcategory_id = db.Column(
        db.Integer, db.ForeignKey("grade_subcategories.id"), nullable=False, index=True
    )
    name = db.Column(db.String(100), nullable=False, index=True)
    weight = db.Column(db.Float, nullable=True)
    max_score = db.Column(db.Float, nullable=False)
    passing_score = db.Column(db.Float, nullable=True)
    position = db.Column(db.Integer, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp(), index=True)

    # Optimized relationships
    subcategory = db.relationship("GradeSubcategory")

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "subcategory_id": self.subcategory_id,
            "name": self.name,
            "weight": self.weight,
            "max_score": self.max_score,
            "passing_score": self.passing_score,
            "position": self.position,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<GradeAssessment {self.name} ({self.max_score} pts)>"


# Class-specific Grading Models
class ClassGradingTemplate(db.Model):
    """Class grading template model - optimized for class-specific grading"""

    __tablename__ = "class_grading_templates"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    class_id = db.Column(
        db.Integer, db.ForeignKey("classes.id"), nullable=False, index=True
    )
    name = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp(), index=True)
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
        index=True,
    )

    # Optimized relationships
    class_obj = db.relationship("Class")
    categories = db.relationship(
        "ClassGradingCategory", back_populates="template", cascade="all, delete-orphan"
    )

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "class_id": self.class_id,
            "name": self.name,
            "description": self.description,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<ClassGradingTemplate {self.name}>"


class ClassGradingCategory(db.Model):
    """Class grading category model - optimized for class-specific categories"""

    __tablename__ = "class_grading_categories"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    template_id = db.Column(
        db.Integer,
        db.ForeignKey("class_grading_templates.id"),
        nullable=False,
        index=True,
    )
    name = db.Column(db.String(50), nullable=False, index=True)
    weight = db.Column(db.Float, nullable=False)
    position = db.Column(db.Integer, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp(), index=True)

    # Optimized relationships
    template = db.relationship("ClassGradingTemplate", back_populates="categories")
    components = db.relationship(
        "ClassGradingComponent", back_populates="category", cascade="all, delete-orphan"
    )

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "template_id": self.template_id,
            "name": self.name,
            "weight": self.weight,
            "position": self.position,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<ClassGradingCategory {self.name} ({self.weight}%)>"


class ClassGradingComponent(db.Model):
    """Class grading component model - optimized for detailed grading components"""

    __tablename__ = "class_grading_components"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category_id = db.Column(
        db.Integer,
        db.ForeignKey("class_grading_categories.id"),
        nullable=False,
        index=True,
    )
    name = db.Column(db.String(100), nullable=False, index=True)
    max_score = db.Column(db.Float, nullable=False)
    weight = db.Column(db.Float, nullable=True)
    position = db.Column(db.Integer, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp(), index=True)

    # Optimized relationships
    category = db.relationship("ClassGradingCategory", back_populates="components")

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "category_id": self.category_id,
            "name": self.name,
            "max_score": self.max_score,
            "weight": self.weight,
            "position": self.position,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<ClassGradingComponent {self.name} ({self.max_score} pts)>"
