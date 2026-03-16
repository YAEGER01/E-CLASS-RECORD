-- Add subject_code column to classes table
ALTER TABLE `classes` ADD COLUMN `subject_code` VARCHAR(50) NULL AFTER `subject`;

-- Optionally, you can remove the schedule column if no longer needed
-- ALTER TABLE `classes` DROP COLUMN `schedule`;
