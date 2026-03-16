# Quick Start Guide - Student Approval System

## Prerequisites
- Database server running (MySQL/MariaDB)
- Python environment set up
- Flask application installed

## Step-by-Step Setup

### 1. Update Database Schema
Run the SQL migration to add approval columns:

```bash
# Connect to your database
mysql -u your_username -p your_database_name

# Run the migration file
source db/add_student_approval_status.sql
```

Or execute directly:
```sql
ALTER TABLE students 
ADD COLUMN approval_status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending' AFTER section,
ADD COLUMN approved_by INT(11) DEFAULT NULL AFTER approval_status,
ADD COLUMN approved_at DATETIME DEFAULT NULL AFTER approved_by,
ADD COLUMN rejection_reason TEXT DEFAULT NULL AFTER approved_at,
ADD INDEX idx_students_approval_status (approval_status),
ADD CONSTRAINT fk_students_approved_by FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE users 
ADD COLUMN account_status ENUM('pending', 'active', 'suspended', 'rejected') DEFAULT 'active' AFTER role,
ADD INDEX idx_users_account_status (account_status);

UPDATE students SET approval_status = 'approved' WHERE approval_status IS NULL OR approval_status = 'pending';
UPDATE users u 
INNER JOIN students s ON u.id = s.user_id 
SET u.account_status = 'active' 
WHERE u.role = 'student' AND (u.account_status IS NULL OR u.account_status = 'pending');
```

### 2. Configure Email Settings

#### Option A: Using PowerShell Script (Recommended for Windows)
```powershell
.\setup_email.ps1
```

#### Option B: Manual Configuration
Create or edit `.env` file in the root directory:

```env
# Email SMTP Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password
SENDER_NAME=E-Class Record System - ISU Cauayan
```

#### Gmail App Password Setup
1. Go to https://myaccount.google.com/security
2. Enable 2-Factor Authentication
3. Go to App passwords: https://myaccount.google.com/apppasswords
4. Select "Mail" and "Windows Computer"
5. Copy the 16-character password (no spaces)
6. Use this as `SENDER_PASSWORD` in .env

### 3. Restart Flask Application
```bash
# Stop the current Flask app (Ctrl+C)
# Then restart
python app.py
```

Or if using the batch file:
```bash
start.bat
```

### 4. Test the System

#### Test Student Registration
1. Go to registration page: `http://localhost:5000/register`
2. Fill out the form completely
3. Submit registration
4. Should see SweetAlert popup: "Registration Pending Approval"
5. Student account is created but cannot log in yet

#### Test Admin Approval
1. Log in as admin: `http://localhost:5000/admin-login`
2. Check "Pending Student Registrations" card
3. Click "Review Registrations" button
4. You should see the test student
5. Click "Approve" button
6. Confirm approval
7. Check that email was sent (check console logs)

#### Test Student Login After Approval
1. Go to student login: `http://localhost:5000/student-login`
2. Use approved student credentials
3. Should successfully log in
4. Check student's email for approval notification

#### Test Rejection (Optional)
1. Register another test student
2. In admin dashboard, click "Reject" instead
3. Optionally enter rejection reason
4. Confirm rejection
5. Try to log in with rejected credentials
6. Should see error message
7. Check student's email for rejection notification

## Troubleshooting

### "Email credentials not configured" Warning
- Make sure `.env` file exists in root directory
- Check that email variables are set correctly
- Restart Flask application after changing .env

### Database Error on Registration
- Verify SQL migration was executed successfully
- Check that both `students` and `users` tables have new columns
- Run: `DESCRIBE students;` and `DESCRIBE users;` to verify

### Pending Count Shows 0
- Check browser console for JavaScript errors
- Verify admin routes are registered
- Test API directly: `http://localhost:5000/admin/pending-registrations`

### Email Not Sending
- Check console logs for detailed error messages
- Verify SMTP credentials are correct
- Test with simple Python script:

```python
import smtplib
from email.mime.text import MIMEText

sender = "your-email@gmail.com"
password = "your-app-password"

msg = MIMEText("Test email")
msg['Subject'] = 'Test'
msg['From'] = sender
msg['To'] = sender

with smtplib.SMTP('smtp.gmail.com', 587) as server:
    server.starttls()
    server.login(sender, password)
    server.send_message(msg)
    print("Email sent successfully!")
```

### SweetAlert Not Showing
- Check browser console for JavaScript errors
- Verify SweetAlert2 CDN is loading
- Check network tab in browser DevTools
- Clear browser cache

## Development Mode (Skip Email)

If you want to test without setting up email:
1. System will log warning but continue working
2. Approval/rejection will work
3. No emails will be sent
4. Check Flask console logs for email content

## Production Checklist

Before deploying to production:
- [ ] Database migration completed
- [ ] Email credentials configured and tested
- [ ] .env file is NOT committed to git (add to .gitignore)
- [ ] Admin account exists and tested
- [ ] Test full registration → approval → login workflow
- [ ] Test rejection workflow
- [ ] Email notifications received successfully
- [ ] Error handling tested
- [ ] SMTP credentials use environment variables
- [ ] Database backups configured

## Support

For issues or questions:
1. Check console logs in Flask application
2. Check browser console for JavaScript errors
3. Verify database schema matches expected structure
4. Review `STUDENT_APPROVAL_SYSTEM.md` for detailed documentation
5. Contact system administrator

## Features Summary

✅ Student registration creates pending account
✅ SweetAlert notification after registration
✅ Admin dashboard shows pending count
✅ Admin can review all pending registrations
✅ Admin can approve with automatic email
✅ Admin can reject with optional reason
✅ Email notifications for both approval/rejection
✅ Students blocked from login until approved
✅ Proper error messages for account status
✅ Database audit trail (approved_by, approved_at)

## Next Steps

After successful setup:
1. Customize email templates in `utils/email_service.py`
2. Adjust SMTP settings for your organization
3. Configure production email server
4. Set up monitoring for failed emails
5. Create admin training documentation
6. Inform students about new registration process
