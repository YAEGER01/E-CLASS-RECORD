-- Migration: Add course-level categories and subcategories for class_id=2 (MAJOR - Networking)
-- Structure id for class_id=2 is assumed to be 3 (verify in your DB before running)

START TRANSACTION;

SET @structure_id = 3;

-- Insert LABORATORY category (course-level weight 40) if not exists
INSERT INTO grade_categories (structure_id, name, weight, position)
SELECT @structure_id, 'LABORATORY', 40, 1
FROM DUAL
WHERE NOT EXISTS (
  SELECT 1 FROM grade_categories WHERE structure_id = @structure_id AND name = 'LABORATORY'
);

-- Get LAB category id
SELECT id INTO @lab_cat_id FROM grade_categories WHERE structure_id = @structure_id AND name = 'LABORATORY' LIMIT 1;

-- Insert LECTURE category (course-level weight 60) if not exists
INSERT INTO grade_categories (structure_id, name, weight, position)
SELECT @structure_id, 'LECTURE', 60, 2
FROM DUAL
WHERE NOT EXISTS (
  SELECT 1 FROM grade_categories WHERE structure_id = @structure_id AND name = 'LECTURE'
);

-- Get LEC category id
SELECT id INTO @lec_cat_id FROM grade_categories WHERE structure_id = @structure_id AND name = 'LECTURE' LIMIT 1;

-- Insert LAB subcategories (weights sum to 100 within LABORATORY)
INSERT INTO grade_subcategories (category_id, name, weight, max_score, position)
SELECT @lab_cat_id, 'Participation', 5, 100, 1
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM grade_subcategories WHERE category_id = @lab_cat_id AND name = 'Participation');

INSERT INTO grade_subcategories (category_id, name, weight, max_score, position)
SELECT @lab_cat_id, 'Homework', 10, 100, 2
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM grade_subcategories WHERE category_id = @lab_cat_id AND name = 'Homework');

INSERT INTO grade_subcategories (category_id, name, weight, max_score, position)
SELECT @lab_cat_id, 'Exercise', 15, 100, 3
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM grade_subcategories WHERE category_id = @lab_cat_id AND name = 'Exercise');

INSERT INTO grade_subcategories (category_id, name, weight, max_score, position)
SELECT @lab_cat_id, 'Prelim Lab Exam', 20, 100, 4
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM grade_subcategories WHERE category_id = @lab_cat_id AND name = 'Prelim Lab Exam');

INSERT INTO grade_subcategories (category_id, name, weight, max_score, position)
SELECT @lab_cat_id, 'Midterm Lab Exam', 25, 100, 5
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM grade_subcategories WHERE category_id = @lab_cat_id AND name = 'Midterm Lab Exam');

INSERT INTO grade_subcategories (category_id, name, weight, max_score, position)
SELECT @lab_cat_id, 'Final Lab Exam', 25, 100, 6
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM grade_subcategories WHERE category_id = @lab_cat_id AND name = 'Final Lab Exam');

-- Insert LECTURE subcategories (weights sum to 100 within LECTURE)
INSERT INTO grade_subcategories (category_id, name, weight, max_score, position)
SELECT @lec_cat_id, 'Attendance', 2.5, 100, 1
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM grade_subcategories WHERE category_id = @lec_cat_id AND name = 'Attendance');

INSERT INTO grade_subcategories (category_id, name, weight, max_score, position)
SELECT @lec_cat_id, 'Attitude', 2.5, 100, 2
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM grade_subcategories WHERE category_id = @lec_cat_id AND name = 'Attitude');

INSERT INTO grade_subcategories (category_id, name, weight, max_score, position)
SELECT @lec_cat_id, 'Recitation', 2.5, 100, 3
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM grade_subcategories WHERE category_id = @lec_cat_id AND name = 'Recitation');

INSERT INTO grade_subcategories (category_id, name, weight, max_score, position)
SELECT @lec_cat_id, 'Homework', 2.5, 100, 4
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM grade_subcategories WHERE category_id = @lec_cat_id AND name = 'Homework');

INSERT INTO grade_subcategories (category_id, name, weight, max_score, position)
SELECT @lec_cat_id, 'Quiz', 15, 100, 5
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM grade_subcategories WHERE category_id = @lec_cat_id AND name = 'Quiz');

INSERT INTO grade_subcategories (category_id, name, weight, max_score, position)
SELECT @lec_cat_id, 'Project', 10, 100, 6
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM grade_subcategories WHERE category_id = @lec_cat_id AND name = 'Project');

INSERT INTO grade_subcategories (category_id, name, weight, max_score, position)
SELECT @lec_cat_id, 'Prelim Exam', 15, 100, 7
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM grade_subcategories WHERE category_id = @lec_cat_id AND name = 'Prelim Exam');

INSERT INTO grade_subcategories (category_id, name, weight, max_score, position)
SELECT @lec_cat_id, 'Midterm Exam', 25, 100, 8
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM grade_subcategories WHERE category_id = @lec_cat_id AND name = 'Midterm Exam');

INSERT INTO grade_subcategories (category_id, name, weight, max_score, position)
SELECT @lec_cat_id, 'Finals Exam', 25, 100, 9
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM grade_subcategories WHERE category_id = @lec_cat_id AND name = 'Finals Exam');

-- Update grade_structures.structure_json to reflect the normalized model (optional but useful)
UPDATE grade_structures
SET structure_json = CONCAT('{"LABORATORY":',
  JSON_QUOTE(JSON_ARRAY(
    JSON_OBJECT('name','Participation','weight',5,'assessments',JSON_ARRAY()),
    JSON_OBJECT('name','Homework','weight',10,'assessments',JSON_ARRAY()),
    JSON_OBJECT('name','Exercise','weight',15,'assessments',JSON_ARRAY()),
    JSON_OBJECT('name','Prelim Lab Exam','weight',20,'assessments',JSON_ARRAY()),
    JSON_OBJECT('name','Midterm Lab Exam','weight',25,'assessments',JSON_ARRAY()),
    JSON_OBJECT('name','Final Lab Exam','weight',25,'assessments',JSON_ARRAY())
  )),
  ',"LECTURE":',
  JSON_QUOTE(JSON_ARRAY(
    JSON_OBJECT('name','Attendance','weight',2.5,'assessments',JSON_ARRAY()),
    JSON_OBJECT('name','Attitude','weight',2.5,'assessments',JSON_ARRAY()),
    JSON_OBJECT('name','Recitation','weight',2.5,'assessments',JSON_ARRAY()),
    JSON_OBJECT('name','Homework','weight',2.5,'assessments',JSON_ARRAY()),
    JSON_OBJECT('name','Quiz','weight',15,'assessments',JSON_ARRAY()),
    JSON_OBJECT('name','Project','weight',10,'assessments',JSON_ARRAY()),
    JSON_OBJECT('name','Prelim Exam','weight',15,'assessments',JSON_ARRAY()),
    JSON_OBJECT('name','Midterm Exam','weight',25,'assessments',JSON_ARRAY()),
    JSON_OBJECT('name','Finals Exam','weight',25,'assessments',JSON_ARRAY())
  )),
  '}')
WHERE id = @structure_id;

-- Insert a new version entry in grade_structure_history
SET @new_version = (SELECT COALESCE(MAX(version),0) + 1 FROM grade_structure_history WHERE structure_id = @structure_id);

INSERT INTO grade_structure_history (structure_id, structure_json, version, changed_by, changed_at)
VALUES (
  @structure_id,
  (SELECT structure_json FROM grade_structures WHERE id = @structure_id),
  @new_version,
  1,
  NOW()
);

COMMIT;

-- End migration
