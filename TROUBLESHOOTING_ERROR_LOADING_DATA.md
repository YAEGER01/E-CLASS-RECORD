# Troubleshooting "Error loading data" in Pending Student Registrations

## The Problem
You're seeing "Error loading data" when clicking the "Review Registrations" button in the admin dashboard.

## Most Likely Cause
**The database migration has not been run yet.** The system is trying to query columns (`approval_status`, `account_status`) that don't exist in your database.

## Solution: Run the Database Migration

### Option 1: Using MySQL Command Line (Recommended)

1. **Open Command Prompt or PowerShell**

2. **Connect to your MySQL database:**
   ```bash
   mysql -u root -p
   ```
   (Replace `root` with your MySQL username)

3. **Select your database:**
   ```sql
   USE your_database_name;
   ```
   (Replace `your_database_name` with your actual database name)

4. **Run the migration:**
   ```sql
   source db/add_student_approval_status.sql
   ```
   
   Or if the above doesn't work, use the full path:
   ```sql
   source C:/Users/USER/Downloads/e class ok na yung major (lab and lecture ng major)/E-CLASS-RECORD-main/db/add_student_approval_status.sql
   ```

5. **Verify the changes:**
   ```sql
   DESCRIBE students;
   DESCRIBE users;
   ```
   
   You should see the new columns:
   - `students` table: `approval_status`, `approved_by`, `approved_at`, `rejection_reason`
   - `users` table: `account_status`

### Option 2: Copy-Paste SQL Commands

If the `source` command doesn't work, copy and paste the SQL directly:

```sql
-- Add approval status and related fields to students table
ALTER TABLE students 
ADD COLUMN approval_status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending' AFTER section,
ADD COLUMN approved_by INT(11) DEFAULT NULL AFTER approval_status,
ADD COLUMN approved_at DATETIME DEFAULT NULL AFTER approved_by,
ADD COLUMN rejection_reason TEXT DEFAULT NULL AFTER approved_at,
ADD INDEX idx_students_approval_status (approval_status),
ADD CONSTRAINT fk_students_approved_by FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL;

-- Add approval status to users table
ALTER TABLE users 
ADD COLUMN account_status ENUM('pending', 'active', 'suspended', 'rejected') DEFAULT 'active' AFTER role,
ADD INDEX idx_users_account_status (account_status);

-- Update existing students to have 'approved' status
UPDATE students SET approval_status = 'approved' WHERE approval_status IS NULL OR approval_status = 'pending';

-- Update existing users to have 'active' account status
UPDATE users u 
INNER JOIN students s ON u.id = s.user_id 
SET u.account_status = 'active' 
WHERE u.role = 'student' AND (u.account_status IS NULL OR u.account_status = 'pending');
```

### Option 3: Using phpMyAdmin or MySQL Workbench

1. Open your database management tool
2. Select your database
3. Go to SQL tab
4. Paste the SQL commands from Option 2
5. Click Execute/Run

## Verify the Fix

### Method 1: Run the Check Script

```bash
python check_approval_system.py
```

This will tell you:
- ✓ Which columns exist
- ✗ Which columns are missing
- How many pending registrations there are

### Method 2: Manual Check

In MySQL:
```sql
DESCRIBE students;
```

Look for these columns:
- `approval_status` ENUM('pending', 'approved', 'rejected')
- `approved_by` INT(11)
- `approved_at` DATETIME
- `rejection_reason` TEXT

```sql
DESCRIBE users;
```

Look for:
- `account_status` ENUM('pending', 'active', 'suspended', 'rejected')

## After Running the Migration

1. **Restart your Flask application**
   - Press `Ctrl+C` in the terminal running Flask
   - Run `python app.py` or `start.bat` again

2. **Refresh the admin dashboard page in your browser**
   - Press `Ctrl+Shift+R` to hard refresh

3. **Try clicking "Review Registrations" again**
   - Should now work without errors
   - Will show "No Pending Registrations" if no students have registered yet

## Testing the System

1. **Register a test student:**
   - Go to: http://localhost:5000/register
   - Fill out the form
   - Submit

2. **Check admin dashboard:**
   - The pending count should show "1"
   - Click "Review Registrations"
   - You should see the test student

3. **Approve or reject the student**
   - Test the approval/rejection workflow

## Still Getting Errors?

### Check Flask Console Logs
Look at the terminal where Flask is running. You should see detailed error messages.

Common errors:
- `column 'approval_status' doesn't exist` → Migration not run
- `Access denied` → Database permission issue
- `Table 'students' doesn't exist` → Wrong database selected

### Check Browser Console
1. Press `F12` in your browser
2. Go to "Console" tab
3. Look for red error messages
4. The error message should now show more details about what went wrong

### Database Connection Issues

If you can't connect to the database:
1. Check if MySQL/MariaDB is running
2. Verify your database credentials in `.env` or `utils/db_conn.py`
3. Make sure the database name is correct

## Need More Help?

Run the diagnostic script:
```bash
python check_approval_system.py
```

This will check everything and tell you exactly what's wrong.

## Quick Reference

**Files involved:**
- Migration: `db/add_student_approval_status.sql`
- Check script: `check_approval_system.py`
- Backend: `blueprints/admin_routes.py`
- Frontend: `templates/admin_dashboard.html`

**Database changes:**
- `students` table: Added 4 columns
- `users` table: Added 1 column
- Both tables: Added indexes
- Foreign key constraint added

**What happens after migration:**
- ✅ Existing students are marked as "approved"
- ✅ Existing users are marked as "active"
- ✅ New registrations will be "pending"
- ✅ Admin can approve/reject registrations
