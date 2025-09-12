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

    def __repr__(self):
        return f'<Instructor {self.user.school_id} - {self.department}>'