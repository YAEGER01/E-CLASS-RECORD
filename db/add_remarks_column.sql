-- Add remarks column to released_grades table
-- This will store the calculated remarks (PASSED, FAILED, NPE, NME, etc.)

ALTER TABLE released_grades 
ADD COLUMN remarks VARCHAR(255) NULL DEFAULT NULL AFTER equivalent;
