# Photo Verification Feature for Student Registration

## Overview
This feature allows administrators to view all student registration information including uploaded verification photos (ID Front, ID Back, and Face Photo) before approving or rejecting student accounts.

## Changes Made

### 1. File Upload Handling in Registration (`blueprints/auth_routes.py`)

#### Added imports and configuration:
```python
import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'static/uploads/student_photos'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
```

#### Updated registration route to:
- Validate uploaded files (ID Front, ID Back, Face Photo)
- Create upload directory if it doesn't exist: `static/uploads/student_photos/`
- Save files with secure filenames using pattern: `{school_id}_{timestamp}_{type}.{extension}`
- Store file paths in database: `id_front_path`, `id_back_path`, `face_photo_path`

Example saved filename: `2021-12345_20240115_143022_id_front.jpg`

### 2. Pending Registrations Endpoint (`blueprints/admin_routes.py`)

#### Updated SQL query to include photo paths:
```sql
SELECT 
    s.id as student_id,
    u.id as user_id,
    u.school_id,
    pi.first_name,
    pi.middle_name,
    pi.last_name,
    pi.email,
    s.course,
    s.track,
    s.year_level,
    s.section,
    s.approval_status,
    s.created_at,
    u.account_status,
    s.id_front_path,      -- NEW
    s.id_back_path,       -- NEW
    s.face_photo_path     -- NEW
FROM students s
INNER JOIN users u ON s.user_id = u.id
INNER JOIN personal_info pi ON s.personal_info_id = pi.id
WHERE s.approval_status = 'pending'
ORDER BY s.created_at DESC
```

#### Added photo paths to response JSON:
```python
"id_front_path": student.get("id_front_path", ""),
"id_back_path": student.get("id_back_path", ""),
"face_photo_path": student.get("face_photo_path", "")
```

### 3. Admin Dashboard UI (`templates/admin_dashboard.html`)

#### Added "View Details" button:
- Blue button with 👁️ icon
- Placed before Approve and Reject buttons
- Calls `viewStudentDetails(studentId)` function

#### Created comprehensive details modal showing:

**Personal Information Section:**
- First Name
- Last Name
- Middle Name
- School ID
- Email Address

**Academic Information Section:**
- Course
- Track (specialization)
- Year Level
- Section
- Registration Date

**Verification Photos Section:**
- ID Front photo (clickable to enlarge)
- ID Back photo (clickable to enlarge)
- Face Photo (clickable to enlarge)
- Warning message to verify photos before approving

**Action Buttons:**
- ✓ Approve Registration (green)
- ✗ Reject Registration (red)

## User Flow

### For Students:
1. Fill out registration form
2. Upload 3 required photos:
   - ID Front (front side of school ID)
   - ID Back (back side of school ID)
   - Face Photo (selfie for identity verification)
3. Submit registration
4. Receive confirmation email
5. Wait for admin approval

### For Administrators:
1. Click "Pending Student Registrations" card on dashboard
2. See list of pending students with summary info
3. Click "👁️ View Details" button for any student
4. Review comprehensive modal with:
   - All personal information
   - Academic details
   - Three verification photos
5. Click photos to view in full size (opens in new tab)
6. Verify student identity by comparing photos
7. Click "✓ Approve Registration" or "✗ Reject Registration"

## File Storage Structure

```
static/
└── uploads/
    └── student_photos/
        ├── 2021-12345_20240115_143022_id_front.jpg
        ├── 2021-12345_20240115_143022_id_back.jpg
        ├── 2021-12345_20240115_143022_face.jpg
        ├── 2021-67890_20240115_150533_id_front.png
        └── ...
```

## File Validation

**Accepted formats:** PNG, JPG, JPEG, WEBP
**Maximum size:** 5MB per file (enforced client-side)
**Required:** All 3 photos must be uploaded before submission

## Database Schema

Photos are stored in the `students` table:
- `id_front_path` VARCHAR - Path to ID front photo
- `id_back_path` VARCHAR - Path to ID back photo
- `face_photo_path` VARCHAR - Path to face photo

Example values: `uploads/student_photos/2021-12345_20240115_143022_id_front.jpg`

## Security Considerations

1. **Filename Security:** Uses `secure_filename()` to prevent directory traversal attacks
2. **File Type Validation:** Checks file extensions against whitelist
3. **File Size Limit:** 5MB maximum enforced in HTML form
4. **Secure Storage:** Files stored in public static folder for easy serving
5. **Database Cascading:** Photos deleted when student record is rejected

## Testing the Feature

1. **Test Registration:**
   - Go to registration page
   - Fill out all fields
   - Upload 3 test photos
   - Submit and verify confirmation email

2. **Test Admin View:**
   - Login as admin
   - Click "Pending Student Registrations"
   - Click "👁️ View Details" on any pending student
   - Verify all information displays correctly
   - Click on photos to test full-size view
   - Test approve/reject from details modal

3. **Test Edge Cases:**
   - Try uploading non-image files (should be rejected)
   - Try submitting without photos (should show validation error)
   - Test with different image formats (PNG, JPG, WEBP)
   - Verify old registrations without photos show "No photo uploaded"

## Troubleshooting

**Photos not displaying:**
- Check if `static/uploads/student_photos/` directory exists
- Verify file paths in database match actual files
- Check file permissions on upload directory

**Upload fails:**
- Verify Flask app has write permissions to static folder
- Check if file size exceeds 5MB
- Ensure file extension is in allowed list

**"No photo uploaded" shown:**
- Check if `id_front_path`, `id_back_path`, `face_photo_path` columns exist in database
- Verify registration route is saving file paths correctly
- Check if student registered before photo feature was added

## Future Enhancements

- Image compression to reduce storage size
- Thumbnail generation for faster loading
- Photo validation (face detection, ID card recognition)
- Bulk photo download for administrators
- Photo deletion when registration is approved (if not needed after approval)
