# Quick Setup Guide

## First Time Setup (5 minutes)

### 1. Setup Virtual Environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configure Database

Create `.env` file in project root:

```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=e_class_record
SECRET_KEY=your-secret-key-here
```

### 3. Create Database

```bash
# In MySQL console or command line
CREATE DATABASE e_class_record;

# Import schema
mysql -u root -p e_class_record < db\e_class_record_backup.sql
```

### 4. Create Admin Account

```bash
python create_admin\create_admin.py
```

Default admin credentials:

- Username: `admin001`
- Password: `Admin123!`

## Running the Application

### Option 1: Quick Start (Recommended)

```powershell
.\start.ps1
```

### Option 2: Manual Start

```powershell
.venv\Scripts\Activate.ps1
python app.py
```

## Access URLs

| Role       | URL                                   |
| ---------- | ------------------------------------- |
| Home       | http://127.0.0.1:5000/                |
| Admin      | http://127.0.0.1:5000/adminlogin      |
| Instructor | http://127.0.0.1:5000/instructorlogin |
| Student    | http://127.0.0.1:5000/studentlogin    |

## Common Commands

### Backup Database

```bash
mysqldump -u root -p e_class_record > db\e_class_record_backup.sql
```

### Run Tests

```bash
pip install -r dev-requirements.txt
pytest
```

### List All Classes (script)

```bash
python scripts\list_classes.py
```

## Troubleshooting

### Port 5000 already in use

Change port in `app.py`:

```python
socketio.run(app, debug=True, port=5001)
```

### Database connection error

- Verify MySQL is running
- Check `.env` credentials
- Ensure database exists

### Module not found

```bash
pip install -r requirements.txt
```

### Virtual environment not activating

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
