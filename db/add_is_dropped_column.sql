-- Add is_dropped column to student_classes table to track dropped status
ALTER TABLE student_classes 
ADD COLUMN is_dropped TINYINT(1) NOT NULL DEFAULT 0;

-- Add index for performance
CREATE INDEX idx_student_classes_dropped ON student_classes(is_dropped);
