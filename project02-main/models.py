import uuid
import hashlib
import random
import string
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')  # student, instructor, admin
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relationship
    student_profile = db.relationship('Student', backref='user', uselist=False, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.school_id}>'

class Student(db.Model):
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course = db.Column(db.String(10), nullable=False)  # BSIT, BSCS, etc.
    track = db.Column(db.String(50), nullable=True)  # Programming, Networking, etc.
    year_level = db.Column(db.Integer, nullable=False)  # 1, 2, 3, 4
    section = db.Column(db.String(10), nullable=False)
    id_front_path = db.Column(db.String(255), nullable=True)
    id_back_path = db.Column(db.String(255), nullable=True)
    face_photo_path = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f'<Student {self.user.school_id} - {self.course}>'

class Instructor(db.Model):
    __tablename__ = 'instructors'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    department = db.Column(db.String(100), nullable=True)
    specialization = db.Column(db.String(100), nullable=True)
    employee_id = db.Column(db.String(20), nullable=True)
    hire_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relationship to classes
    classes = db.relationship('Class', backref='instructor', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Instructor {self.user.school_id} - {self.department}>'


def generate_class_codes():
    """Generate unique 36-character class code and 6-digit join code"""
    # Generate 36-character encrypted code using UUID
    class_code = str(uuid.uuid4())

    # Generate 6-digit join code from hash of the class_code
    hash_obj = hashlib.md5(class_code.encode())
    hash_hex = hash_obj.hexdigest()
    # Take first 6 characters and convert to digits only
    join_code = ''.join(c for c in hash_hex[:6] if c.isdigit())
    # If not enough digits, pad with random digits
    while len(join_code) < 6:
        join_code += str(random.randint(0, 9))

    return class_code, join_code[:6]  # Ensure exactly 6 digits


class Class(db.Model):
    __tablename__ = 'classes'

    id = db.Column(db.Integer, primary_key=True)
    instructor_id = db.Column(db.Integer, db.ForeignKey('instructors.id'), nullable=False)
    year = db.Column(db.String(4), nullable=False)  # e.g., "2024", "2025"
    semester = db.Column(db.String(20), nullable=False)  # e.g., "1st sem", "2nd sem"
    course = db.Column(db.String(10), nullable=False)  # e.g., "BSIT", "BSCS"
    track = db.Column(db.String(50), nullable=False)  # e.g., "Programming", "Networking"
    section = db.Column(db.String(10), nullable=False)  # e.g., "1A", "2B"
    schedule = db.Column(db.String(50), nullable=False)  # e.g., "M-W-F 8-10AM"
    class_code = db.Column(db.String(36), unique=True, nullable=False)  # 36-char encrypted unique code
    join_code = db.Column(db.String(6), unique=True, nullable=False)  # 6-digit code for students
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    def __repr__(self):
        return f'<Class {self.year}-{self.semester} {self.course} {self.section}>'

    @property
    def class_id(self):
        """Generate formatted class ID like '24-1 BSIT 1A'"""
        formatted_year = self.year[-2:]  # Last 2 digits of year
        formatted_semester = '1' if '1st' in self.semester.lower() else '2' if '2nd' in self.semester.lower() else self.semester
        return f"{formatted_year}-{formatted_semester} {self.course} {self.section}"


class StudentClass(db.Model):
    """Model for student-class enrollments (many-to-many relationship)"""
    __tablename__ = 'student_classes'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relationships
    student = db.relationship('Student', backref='enrollments')
    class_obj = db.relationship('Class', backref='enrollments')

    # Constraints
    __table_args__ = (
        db.UniqueConstraint('student_id', 'class_id', name='unique_student_class'),
    )

    def __repr__(self):
        return f'<StudentClass student:{self.student_id} class:{self.class_id}>'