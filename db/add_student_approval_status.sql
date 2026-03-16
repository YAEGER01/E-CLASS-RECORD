-- Add approval status and related fields to students table
ALTER TABLE students 
ADD COLUMN approval_status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending' AFTER section,
ADD COLUMN approved_by INT(11) DEFAULT NULL AFTER approval_status,
ADD COLUMN approved_at DATETIME DEFAULT NULL AFTER approved_by,
ADD COLUMN rejection_reason TEXT DEFAULT NULL AFTER approved_at,
ADD INDEX idx_students_approval_status (approval_status),
ADD CONSTRAINT fk_students_approved_by FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL;

-- Add approval status to users table to disable login for pending accounts
ALTER TABLE users 
ADD COLUMN account_status ENUM('pending', 'active', 'suspended', 'rejected') DEFAULT 'active' AFTER role,
ADD INDEX idx_users_account_status (account_status);

-- Update existing students to have 'approved' status and 'active' account status
UPDATE students SET approval_status = 'approved' WHERE approval_status IS NULL OR approval_status = 'pending';
UPDATE users u 
INNER JOIN students s ON u.id = s.user_id 
SET u.account_status = 'active' 
WHERE u.role = 'student' AND (u.account_status IS NULL OR u.account_status = 'pending');
