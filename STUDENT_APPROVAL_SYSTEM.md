# Student Registration Approval System

## Overview
This system implements an approval workflow for student registrations. When students register, their accounts are placed in a "pending" state until an administrator approves or rejects them. Students receive email notifications about their registration status.

## New Features

### 1. **Pending Registration Status**
- Student accounts are created with `approval_status = 'pending'`
- User accounts have `account_status = 'pending'` 
- Students cannot log in until their account is approved

### 2. **Admin Dashboard Integration**
- New card showing count of pending registrations
- "Review Registrations" button to manage pending accounts
- Real-time count updates

### 3. **Approval/Rejection Workflow**
- Administrators can:
  - View all pending student registrations
  - Approve individual registrations
  - Reject registrations with optional reason
  - Email notifications sent automatically

### 4. **Email Notifications**
- **Approval Email**: Sent when admin approves registration
  - Includes account details
  - Link to login page
- **Rejection Email**: Sent when admin rejects registration
  - Includes optional rejection reason
  - Contact information for support

### 5. **Registration Page Updates**
- SweetAlert2 popup after successful registration submission
- Informs students their account is pending approval
- Explains they will receive email notification

## Database Changes

### SQL Migration Required
Run the following SQL migration to add the required fields:

```sql
-- File: db/add_student_approval_status.sql
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

-- Update existing students to have 'approved' status
UPDATE students SET approval_status = 'approved' WHERE approval_status IS NULL OR approval_status = 'pending';
UPDATE users u 
INNER JOIN students s ON u.id = s.user_id 
SET u.account_status = 'active' 
WHERE u.role = 'student' AND (u.account_status IS NULL OR u.account_status = 'pending');
```

## Email Configuration

### Environment Variables
Set up the following environment variables for email notifications:

```bash
# Email SMTP Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password
SENDER_NAME=E-Class Record System - ISU Cauayan
```

### Gmail Setup (Recommended)
1. Go to your Google Account settings
2. Enable 2-Factor Authentication
3. Generate an App Password:
   - Go to Security → App passwords
   - Select "Mail" and "Windows Computer"
   - Copy the generated 16-character password
4. Use this app password as `SENDER_PASSWORD`

### Alternative SMTP Providers
You can use any SMTP provider:
- **Outlook/Hotmail**: `smtp-mail.outlook.com:587`
- **Yahoo**: `smtp.mail.yahoo.com:587`
- **Custom**: Configure your organization's SMTP server

## API Endpoints

### Get Pending Registrations
```
GET /admin/pending-registrations
Authorization: Admin role required
Response: {
    "success": true,
    "students": [...]
}
```

### Approve Registration
```
POST /admin/approve-registration/<student_id>
Authorization: Admin role required
Response: {
    "success": true,
    "message": "Student registration approved successfully",
    "email_sent": true
}
```

### Reject Registration
```
POST /admin/reject-registration/<student_id>
Authorization: Admin role required
Body: {
    "reason": "Optional rejection reason"
}
Response: {
    "success": true,
    "message": "Student registration rejected",
    "email_sent": true
}
```

## Usage Guide

### For Students
1. Fill out the registration form completely
2. Submit the form
3. See confirmation popup about pending approval
4. Wait for email notification
5. Once approved, log in with credentials

### For Administrators
1. Log in to admin dashboard
2. Check "Pending Student Registrations" card
3. Click "Review Registrations" button
4. Review student information
5. Click "Approve" or "Reject" for each student
6. Optionally provide rejection reason
7. Student receives automatic email notification

## Testing

### Test Without Email (Development)
If email credentials are not configured:
- System will log a warning
- Approval/rejection will still work
- No emails will be sent
- Check console logs for email content

### Test With Email
1. Configure environment variables
2. Register a test student account
3. Approve/reject from admin dashboard
4. Check email inbox for notification

## Files Modified/Created

### New Files
- `utils/email_service.py` - Email notification service
- `db/add_student_approval_status.sql` - Database migration

### Modified Files
- `blueprints/auth_routes.py` - Registration and login logic
- `blueprints/admin_routes.py` - Admin approval endpoints
- `templates/admin_dashboard.html` - Pending registrations UI
- `templates/register.html` - Pending approval SWAL popup

## Troubleshooting

### Students Can't Log In
- Check `account_status` in `users` table
- Should be 'active' for approved students
- Verify `approval_status` in `students` table is 'approved'

### Emails Not Sending
- Verify environment variables are set
- Check SMTP credentials are correct
- Review console logs for error messages
- Test SMTP connection independently

### Pending Count Not Updating
- Check browser console for JavaScript errors
- Verify API endpoint is accessible
- Check database for pending registrations

## Security Considerations

1. **Email Credentials**: Store in environment variables, never commit to git
2. **CSRF Protection**: All forms include CSRF tokens
3. **Admin Authorization**: All endpoints verify admin role
4. **SQL Injection**: Using parameterized queries
5. **Password Security**: Using werkzeug password hashing

## Future Enhancements

Potential improvements:
- Bulk approve/reject functionality
- Email templates customization
- SMS notifications
- Audit log for approval actions
- Filtering and search in pending registrations
- Export pending registrations to CSV
- Integration with student information system
