# E-Class Record System 📚

A comprehensive academic grade management system with real-time updates, automated grade computation, and secure role-based access control.

## Features

- **Admin Dashboard**: Complete system oversight and user management
- **Instructor Portal**: Class creation, assessment management, and automated grade computation
- **Student Portal**: Real-time grade viewing and academic progress tracking
- **Security**: Role-based authentication, CSRF protection, password hashing
- **Real-time Updates**: WebSocket-based live grade updates
- **PDF Reports**: Generate professional grade reports
- **Obfuscated URLs**: Non-sequential, secure URL patterns for privacy

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: MySQL with PyMySQL
- **Frontend**: HTML/CSS/JavaScript
- **Real-time**: Flask-SocketIO
- **Security**: Flask-WTF, Werkzeug, Cryptography
- **Analytics**: NumPy, Scikit-learn
- **Reports**: ReportLab, WeasyPrint

## Quick Start

### Prerequisites

- Python 3.8+
- MySQL Server
- Virtual environment (recommended)

### Installation

1. **Clone or navigate to the project directory**

   ```bash
   cd C:\Users\maday\PROJECTS\E-CLASS-RECORD
   ```

2. **(Optional) Create and activate virtual environment**

   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

3. **Install dependencies** (Python 3.8–3.13 supported)

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure database**

   - Create MySQL database: `e_class_record`
   - Update `.env` file with your database credentials:
     ```
     DB_HOST=localhost
     DB_USER=root
     DB_PASSWORD=your_password
     DB_NAME=e_class_record
     SECRET_KEY=your_secret_key
     ```

5. **Initialize database**

   ```bash
   # Import the database schema
   mysql -u root -p e_class_record < db\e_class_record_backup.sql
   ```

6. **Create admin account**
   ```bash
   python create_admin\create_admin.py
   ```
   Default credentials:
   - Username: `admin001`
   - Password: `Admin123!`

### Running the Application

```bash
python app.py
```

The application will be available at: `http://127.0.0.1:5000`

### Access Points

- **Admin Login**: `http://127.0.0.1:5000/adminlogin`
- **Instructor Login**: `http://127.0.0.1:5000/instructorlogin`
- **Student Login**: `http://127.0.0.1:5000/studentlogin`
- **Home**: `http://127.0.0.1:5000/`

## Development

### Running Tests

```bash
pip install -r dev-requirements.txt
pytest
```

### Project Structure

```
E-CLASS-RECORD/
├── app.py                  # Main application entry point
├── blueprints/            # Route modules
│   ├── admin_routes.py
│   ├── instructor_routes.py
│   ├── student_routes.py
│   └── ...
├── utils/                 # Utility modules
│   ├── db_conn.py        # Database connection
│   ├── grade_calculation.py
│   ├── auth_utils.py
│   └── ...
├── templates/             # HTML templates
├── static/               # CSS, JS, images
├── db/                   # Database backups
├── tests/                # Test suite
└── requirements.txt      # Dependencies
```

## User Roles

1. **Admin**: System-wide management and oversight
2. **Instructor**: Class and grade management
3. **Student**: View grades and academic progress

## Security Features

- Role-based access control (RBAC)
- CSRF protection on all forms
- Password hashing with Werkzeug
- Secure session management
- SQL injection prevention
- Obfuscated URL patterns

## Database Backup

To backup the database:

```bash
mysqldump -u root -p e_class_record > db\e_class_record_backup.sql
```

## Troubleshooting

### Common Issues

1. **Database connection error**: Check MySQL is running and credentials in `.env` are correct
2. **Module not found**: Ensure virtual environment is activated and dependencies are installed
3. **Port already in use**: Change the port in `app.py` or stop the conflicting process

### Support

For issues or questions, check the TODO.md file or review the code documentation.
