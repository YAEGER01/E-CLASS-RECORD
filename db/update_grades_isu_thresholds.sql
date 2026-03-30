-- Update released grades with new ISU thresholds
-- New Thresholds:
-- 98+ → 1.0
-- 95+ → 1.25  
-- 92+ → 1.5
-- 89+ → 1.75
-- 86+ → 2.0
-- 83+ → 2.25
-- 80+ → 2.5
-- 77+ → 2.75
-- 75+ → 3.0
-- <75 → 5.0

UPDATE released_grades
SET equivalent = CASE
    WHEN final_grade >= 98 THEN '1.0'
    WHEN final_grade >= 95 THEN '1.25'
    WHEN final_grade >= 92 THEN '1.5'
    WHEN final_grade >= 89 THEN '1.75'
    WHEN final_grade >= 86 THEN '2.0'
    WHEN final_grade >= 83 THEN '2.25'
    WHEN final_grade >= 80 THEN '2.5'
    WHEN final_grade >= 77 THEN '2.75'
    WHEN final_grade >= 75 THEN '3.0'
    ELSE '5.0'
END
WHERE final_grade IS NOT NULL AND equivalent IS NOT NULL;

-- Verify the update
SELECT final_grade, equivalent, COUNT(*) as count 
FROM released_grades 
WHERE final_grade IS NOT NULL 
GROUP BY final_grade, equivalent 
ORDER BY final_grade DESC;
