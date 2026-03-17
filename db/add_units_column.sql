-- Migration: Add units column to classes table
-- This allows tracking of subject units (e.g., 3, 3.0, 2.5, etc.)

-- Add units column to classes table
ALTER TABLE `classes` 
ADD COLUMN `units` DECIMAL(4,1) NULL DEFAULT NULL AFTER `subject_code`;

-- Optional: Add comment for documentation
ALTER TABLE `classes` 
MODIFY COLUMN `units` DECIMAL(4,1) NULL DEFAULT NULL COMMENT 'Subject units (e.g., 3.0, 2.5)';
