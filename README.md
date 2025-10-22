# E-Class Record System

A comprehensive web-based class record management system built with Python Flask, designed for educational institutions to manage student records, instructor classes, and grading systems.

## Features

### For Students

- **Secure Login**: Role-based authentication with school ID and password
- **Class Enrollment**: Join classes using unique join codes provided by instructors
- **Dashboard**: View enrolled classes and personal information
- **Profile Management**: Update personal details and academic information

### For Instructors

- **Class Management**: Create and manage multiple classes with unique codes
- **Student Oversight**: View enrolled students and class statistics
- **Grade Builder**: Design custom grading structures with categories and assessments
- **Version Control**: Track changes to grading structures with history and restoration

### For Administrators

- **User Management**: Create and manage instructor accounts
- **System Oversight**: Monitor all users, classes, and system analytics
- **Account Control**: Suspend or reactivate instructor accounts as needed

## Technology Stack

- **Backend**: Python Flask with MySQL database
- **Frontend**: HTML5, CSS3, JavaScript
- **Security**: CSRF protection, password hashing, session management
- **Database**: MySQL with foreign key relationships
- **Deployment**: Ready for production deployment

## Project Structure

```
project02-main/
├── app.py                 # Main Flask application
├── db_conn.py            # Database connection utilities
├── pyproject.toml        # Project configuration
├── requirements.txt      # Production dependencies
├── dev-requirements.txt  # Development dependencies
├── db/
│   └── e_class_record.sql # Database schema and sample data
├── src/                  # Source code directory
├── static/               # Static assets (CSS, JS, images)
│   ├── css/             # Stylesheets
│   ├── js/              # JavaScript files
│   └── images/          # Image assets
├── templates/            # Jinja2 templates
│   ├── base.html        # Base template
│   ├── login.html       # Login page
│   ├── admin_dashboard.html
│   ├── instructor_dashboard.html
│   ├── student_dashboard.html
│   └── ...              # Other templates
└── tests/               # Test files
```

## Database Schema

The system uses a relational MySQL database with the following key tables:

- **users**: Authentication and role management
- **personal_info**: User personal details
- **students**: Student-specific information
- **instructors**: Instructor profiles and details
- **classes**: Class information with unique codes
- **student_classes**: Enrollment relationships
- **grade_structures**: Grading templates and configurations
- **grade_structure_history**: Version control for grading structures
- **grade_categories**: Grading category definitions
- **grade_subcategories**: Detailed assessment components
- **assessments**: Individual assessment items
- **student_grades**: Student performance records

## Installation and Setup

### Prerequisites

- Python 3.10 or higher
- MySQL Server
- VS Code (recommended) with Python extensions

### Setup Steps

1. **Clone the repository**:

   ```bash
   git clone <repository-url>
   cd e-class-record
   ```

2. **Create virtual environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   pip install -r dev-requirements.txt  # For development
   ```

4. **Setup database**:

   - Create a MySQL database named `e_class_record`
   - Import the schema: `mysql -u username -p e_class_record < db/e_class_record.sql`

5. **Configure database connection**:
   Update `db_conn.py` with your MySQL credentials

6. **Run the application**:

   ```bash
   python app.py
   ```

7. **Access the application**:
   Open http://localhost:5000 in your browser

## Usage

### Default Accounts

- **Admin**: school_id: `admin001`, password: Admin123!
- **Instructor**: school_id: `CL-002`, password: Cl-002
- **Student**: school_id: `23-13439`, password: iforgor

### Creating Classes (Instructors)

1. Log in as an instructor
2. Navigate to "My Classes"
3. Click "Create New Class"
4. Fill in class details (year, semester, course, section, schedule)
5. Share the generated join code with students

### Joining Classes (Students)

1. Log in as a student
2. Use the join code provided by your instructor
3. Confirm enrollment

### Grade Builder (Instructors)

1. Access the Grade Builder from your dashboard
2. Select a class
3. Design grading categories and assessments
4. Save and apply to student grading

## API Endpoints

The system provides RESTful API endpoints for:

- User authentication and management
- Class creation and enrollment
- Grade structure management
- Student and instructor data retrieval

## Security Features

- **Password Hashing**: Secure password storage using Werkzeug
- **CSRF Protection**: Cross-site request forgery prevention
- **Session Management**: Secure session handling
- **Role-based Access**: Different permissions for admin, instructor, and student roles
- **Input Validation**: Comprehensive form validation and sanitization

## Development

### Running Tests

```bash
pytest
```

### Code Style

This project follows PEP 8 Python style guidelines and includes basic security practices.

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please contact the development team or create an issue in the repository.
