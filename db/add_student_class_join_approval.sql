-- Migration: Add approval system for student class joins
-- This adds a status column to track pending/approved/rejected join requests

-- Add status column to student_classes table
ALTER TABLE student_classes 
ADD COLUMN status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending' AFTER joined_at,
ADD COLUMN approved_by INT(11) DEFAULT NULL AFTER status,
ADD COLUMN approved_at DATETIME DEFAULT NULL AFTER approved_by,
ADD COLUMN rejection_reason TEXT DEFAULT NULL AFTER approved_at,
ADD INDEX idx_status (status),
ADD INDEX idx_approved_by (approved_by);

-- Add foreign key for approved_by (references instructors table)
ALTER TABLE student_classes
ADD CONSTRAINT fk_student_classes_approved_by 
FOREIGN KEY (approved_by) REFERENCES instructors(id) ON DELETE SET NULL;

-- Update existing records to 'approved' status (backwards compatibility)
UPDATE student_classes SET status = 'approved', approved_at = joined_at WHERE status = 'pending';
