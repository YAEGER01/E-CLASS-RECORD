/*
SQLyog Ultimate v13.1.1 (64 bit)
MySQL - 12.0.2-MariaDB : Database - e_class_record
*********************************************************************
*/

/*!40101 SET NAMES utf8 */;

/*!40101 SET SQL_MODE=''*/;

/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
CREATE DATABASE /*!32312 IF NOT EXISTS*/`e_class_record` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci */;

USE `e_class_record`;

/*Table structure for table `classes` */

DROP TABLE IF EXISTS `classes`;

CREATE TABLE `classes` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `instructor_id` int(11) NOT NULL,
  `class_type` varchar(10) DEFAULT NULL,
  `year` varchar(4) NOT NULL,
  `semester` varchar(20) NOT NULL,
  `course` varchar(10) NOT NULL,
  `subject` varchar(100) NOT NULL,
  `subject_code` varchar(50) DEFAULT NULL,
  `units` decimal(4,1) DEFAULT NULL COMMENT 'Subject units (e.g., 3.0, 2.5)',
  `track` varchar(50) NOT NULL,
  `section` varchar(10) NOT NULL,
  `schedule` varchar(50) NOT NULL,
  `class_code` varchar(36) NOT NULL,
  `join_code` varchar(6) NOT NULL,
  `grading_template_id` int(11) DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `class_code` (`class_code`),
  UNIQUE KEY `join_code` (`join_code`),
  KEY `idx_classes_instructor_id` (`instructor_id`),
  KEY `idx_classes_year` (`year`),
  KEY `idx_classes_semester` (`semester`),
  KEY `idx_classes_course` (`course`),
  KEY `idx_classes_track` (`track`),
  KEY `idx_classes_section` (`section`),
  KEY `idx_classes_class_code` (`class_code`),
  KEY `idx_classes_join_code` (`join_code`),
  CONSTRAINT `classes_ibfk_1` FOREIGN KEY (`instructor_id`) REFERENCES `instructors` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Data for the table `classes` */

/*Table structure for table `grade_assessments` */

DROP TABLE IF EXISTS `grade_assessments`;

CREATE TABLE `grade_assessments` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `subcategory_id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `weight` float DEFAULT NULL,
  `max_score` float NOT NULL,
  `passing_score` float DEFAULT NULL,
  `position` int(11) NOT NULL,
  `description` text DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_grade_assessments_subcategory_id` (`subcategory_id`),
  KEY `idx_grade_assessments_name` (`name`),
  KEY `idx_grade_assessments_position` (`position`),
  CONSTRAINT `fk_subcategory` FOREIGN KEY (`subcategory_id`) REFERENCES `grade_subcategories` (`id`) ON DELETE CASCADE,
  CONSTRAINT `grade_assessments_ibfk_1` FOREIGN KEY (`subcategory_id`) REFERENCES `grade_subcategories` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Data for the table `grade_assessments` */

/*Table structure for table `grade_calculation_templates` */

DROP TABLE IF EXISTS `grade_calculation_templates`;

CREATE TABLE `grade_calculation_templates` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `description` text DEFAULT NULL,
  `template_json` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL CHECK (json_valid(`template_json`)),
  `is_default` tinyint(1) DEFAULT 0,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Data for the table `grade_calculation_templates` */

/*Table structure for table `grade_categories` */

DROP TABLE IF EXISTS `grade_categories`;

CREATE TABLE `grade_categories` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `structure_id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `weight` float NOT NULL,
  `position` int(11) NOT NULL,
  `description` text DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_grade_categories_structure_id` (`structure_id`),
  KEY `idx_grade_categories_name` (`name`),
  KEY `idx_grade_categories_position` (`position`),
  CONSTRAINT `fk_structure` FOREIGN KEY (`structure_id`) REFERENCES `grade_structures` (`id`) ON DELETE CASCADE,
  CONSTRAINT `grade_categories_ibfk_1` FOREIGN KEY (`structure_id`) REFERENCES `grade_structures` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Data for the table `grade_categories` */

/*Table structure for table `grade_sheet_signatures` */

DROP TABLE IF EXISTS `grade_sheet_signatures`;

CREATE TABLE `grade_sheet_signatures` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `class_id` int(11) NOT NULL,
  `submitted_by_name` varchar(255) DEFAULT NULL,
  `submitted_by_title` varchar(255) DEFAULT 'Assistant Professor IV',
  `checked_by_name` varchar(255) DEFAULT NULL,
  `checked_by_title` varchar(255) DEFAULT 'Chair, BSIT',
  `countersigned_by_name` varchar(255) DEFAULT NULL,
  `countersigned_by_title` varchar(255) DEFAULT 'College Secretary',
  `noted_by_name` varchar(255) DEFAULT NULL,
  `noted_by_title` varchar(255) DEFAULT 'Dean, CCSICT',
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_class_signature` (`class_id`),
  KEY `idx_class_id` (`class_id`),
  CONSTRAINT `grade_sheet_signatures_ibfk_1` FOREIGN KEY (`class_id`) REFERENCES `classes` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Data for the table `grade_sheet_signatures` */

/*Table structure for table `grade_snapshots` */

DROP TABLE IF EXISTS `grade_snapshots`;

CREATE TABLE `grade_snapshots` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `class_id` int(11) NOT NULL,
  `version` int(11) NOT NULL,
  `status` enum('draft','final') NOT NULL DEFAULT 'draft',
  `snapshot_json` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL CHECK (json_valid(`snapshot_json`)),
  `created_by` int(11) NOT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `released_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_class_version` (`class_id`,`version`),
  KEY `idx_class_status` (`class_id`,`status`),
  CONSTRAINT `fk_snapshots_class` FOREIGN KEY (`class_id`) REFERENCES `classes` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Data for the table `grade_snapshots` */

/*Table structure for table `grade_structure_history` */

DROP TABLE IF EXISTS `grade_structure_history`;

CREATE TABLE `grade_structure_history` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `structure_id` int(11) NOT NULL,
  `structure_json` text NOT NULL,
  `version` int(11) NOT NULL,
  `changed_by` int(11) NOT NULL,
  `changed_at` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `changed_by` (`changed_by`),
  KEY `idx_structure_id` (`structure_id`),
  KEY `idx_version` (`version`),
  KEY `idx_changed_at` (`changed_at`),
  CONSTRAINT `grade_structure_history_ibfk_1` FOREIGN KEY (`structure_id`) REFERENCES `grade_structures` (`id`) ON DELETE CASCADE,
  CONSTRAINT `grade_structure_history_ibfk_2` FOREIGN KEY (`changed_by`) REFERENCES `instructors` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Data for the table `grade_structure_history` */

/*Table structure for table `grade_structures` */

DROP TABLE IF EXISTS `grade_structures`;

CREATE TABLE `grade_structures` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `class_id` int(11) NOT NULL,
  `structure_name` varchar(100) NOT NULL,
  `structure_json` text NOT NULL,
  `created_by` int(11) NOT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `is_active` tinyint(1) DEFAULT 1,
  `version` int(11) NOT NULL DEFAULT 1,
  PRIMARY KEY (`id`),
  KEY `idx_grade_structures_class_id` (`class_id`),
  KEY `idx_grade_structures_structure_name` (`structure_name`),
  KEY `idx_grade_structures_created_by` (`created_by`),
  KEY `idx_grade_structures_is_active` (`is_active`),
  CONSTRAINT `grade_structures_ibfk_1` FOREIGN KEY (`class_id`) REFERENCES `classes` (`id`) ON DELETE CASCADE,
  CONSTRAINT `grade_structures_ibfk_2` FOREIGN KEY (`created_by`) REFERENCES `instructors` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Data for the table `grade_structures` */

/*Table structure for table `grade_subcategories` */

DROP TABLE IF EXISTS `grade_subcategories`;

CREATE TABLE `grade_subcategories` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `category_id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `weight` float DEFAULT NULL,
  `max_score` float NOT NULL,
  `passing_score` float DEFAULT NULL,
  `position` int(11) NOT NULL,
  `description` text DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_grade_subcategories_category_id` (`category_id`),
  KEY `idx_grade_subcategories_name` (`name`),
  KEY `idx_grade_subcategories_position` (`position`),
  CONSTRAINT `fk_category` FOREIGN KEY (`category_id`) REFERENCES `grade_categories` (`id`) ON DELETE CASCADE,
  CONSTRAINT `grade_subcategories_ibfk_1` FOREIGN KEY (`category_id`) REFERENCES `grade_categories` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Data for the table `grade_subcategories` */

/*Table structure for table `instructors` */

DROP TABLE IF EXISTS `instructors`;

CREATE TABLE `instructors` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `personal_info_id` int(11) DEFAULT NULL,
  `department` varchar(100) DEFAULT NULL,
  `specialization` varchar(100) DEFAULT NULL,
  `employee_id` varchar(20) DEFAULT NULL,
  `hire_date` date DEFAULT NULL,
  `status` varchar(20) NOT NULL DEFAULT 'active',
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `employee_id` (`employee_id`),
  KEY `idx_instructors_user_id` (`user_id`),
  KEY `idx_instructors_personal_info_id` (`personal_info_id`),
  KEY `idx_instructors_department` (`department`),
  KEY `idx_instructors_employee_id` (`employee_id`),
  KEY `idx_instructors_hire_date` (`hire_date`),
  KEY `idx_instructors_status` (`status`),
  CONSTRAINT `instructors_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `instructors_ibfk_2` FOREIGN KEY (`personal_info_id`) REFERENCES `personal_info` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Data for the table `instructors` */

/*Table structure for table `password_reset_tokens` */

DROP TABLE IF EXISTS `password_reset_tokens`;

CREATE TABLE `password_reset_tokens` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `token` varchar(255) NOT NULL,
  `role` enum('student','instructor') NOT NULL,
  `expires_at` datetime NOT NULL,
  `used` tinyint(1) DEFAULT 0,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `token` (`token`),
  KEY `idx_token` (`token`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_expires_at` (`expires_at`),
  CONSTRAINT `password_reset_tokens_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Data for the table `password_reset_tokens` */

/*Table structure for table `personal_info` */

DROP TABLE IF EXISTS `personal_info`;

CREATE TABLE `personal_info` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `first_name` varchar(50) NOT NULL,
  `last_name` varchar(50) NOT NULL,
  `middle_name` varchar(50) DEFAULT NULL,
  `email` varchar(100) NOT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `address` varchar(255) DEFAULT NULL,
  `birth_date` date DEFAULT NULL,
  `gender` varchar(10) DEFAULT NULL,
  `emergency_contact_name` varchar(100) DEFAULT NULL,
  `emergency_contact_phone` varchar(20) DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`),
  KEY `idx_personal_info_first_name` (`first_name`),
  KEY `idx_personal_info_last_name` (`last_name`),
  KEY `idx_personal_info_email` (`email`),
  KEY `idx_personal_info_phone` (`phone`),
  KEY `idx_personal_info_birth_date` (`birth_date`),
  KEY `idx_personal_info_gender` (`gender`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Data for the table `personal_info` */

/*Table structure for table `professor_calculation_overrides` */

DROP TABLE IF EXISTS `professor_calculation_overrides`;

CREATE TABLE `professor_calculation_overrides` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `professor_id` int(11) NOT NULL,
  `class_id` int(11) DEFAULT NULL,
  `name` varchar(100) NOT NULL,
  `description` text DEFAULT NULL,
  `template_json` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL CHECK (json_valid(`template_json`)),
  `is_active` tinyint(1) DEFAULT 0,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `professor_id` (`professor_id`),
  KEY `class_id` (`class_id`),
  CONSTRAINT `professor_calculation_overrides_ibfk_1` FOREIGN KEY (`professor_id`) REFERENCES `instructors` (`id`),
  CONSTRAINT `professor_calculation_overrides_ibfk_2` FOREIGN KEY (`class_id`) REFERENCES `classes` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Data for the table `professor_calculation_overrides` */

/*Table structure for table `released_grades` */

DROP TABLE IF EXISTS `released_grades`;

CREATE TABLE `released_grades` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `class_id` int(11) NOT NULL,
  `snapshot_id` int(11) NOT NULL,
  `student_id` int(11) NOT NULL,
  `student_school_id` varchar(20) DEFAULT NULL,
  `student_name` varchar(255) DEFAULT NULL,
  `final_grade` decimal(5,2) DEFAULT NULL,
  `equivalent` varchar(10) DEFAULT NULL,
  `remarks` varchar(255) DEFAULT NULL,
  `overall_percentage` decimal(6,3) DEFAULT NULL,
  `status` varchar(20) NOT NULL DEFAULT 'released',
  `grade_payload` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL CHECK (json_valid(`grade_payload`)),
  `released_by` int(11) DEFAULT NULL,
  `released_at` datetime DEFAULT current_timestamp(),
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_released_grades_class_student` (`class_id`,`student_id`),
  KEY `idx_released_grades_snapshot_id` (`snapshot_id`),
  KEY `idx_released_grades_status` (`status`),
  KEY `idx_released_grades_released_at` (`released_at`),
  KEY `released_grades_student_fk` (`student_id`),
  KEY `released_grades_user_fk` (`released_by`),
  CONSTRAINT `released_grades_class_fk` FOREIGN KEY (`class_id`) REFERENCES `classes` (`id`) ON DELETE CASCADE,
  CONSTRAINT `released_grades_snapshot_fk` FOREIGN KEY (`snapshot_id`) REFERENCES `grade_snapshots` (`id`) ON DELETE CASCADE,
  CONSTRAINT `released_grades_student_fk` FOREIGN KEY (`student_id`) REFERENCES `students` (`id`) ON DELETE CASCADE,
  CONSTRAINT `released_grades_user_fk` FOREIGN KEY (`released_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Data for the table `released_grades` */

/*Table structure for table `student_classes` */

DROP TABLE IF EXISTS `student_classes`;

CREATE TABLE `student_classes` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `student_id` int(11) NOT NULL,
  `class_id` int(11) NOT NULL,
  `joined_at` datetime DEFAULT current_timestamp(),
  `status` enum('pending','approved','rejected') DEFAULT 'pending',
  `approved_by` int(11) DEFAULT NULL,
  `approved_at` datetime DEFAULT NULL,
  `rejection_reason` text DEFAULT NULL,
  `is_dropped` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_student_class` (`student_id`,`class_id`),
  KEY `idx_student_classes_student_id` (`student_id`),
  KEY `idx_student_classes_class_id` (`class_id`),
  KEY `idx_student_classes_joined_at` (`joined_at`),
  KEY `idx_status` (`status`),
  KEY `idx_approved_by` (`approved_by`),
  KEY `idx_student_classes_dropped` (`is_dropped`),
  CONSTRAINT `fk_student_classes_approved_by` FOREIGN KEY (`approved_by`) REFERENCES `instructors` (`id`) ON DELETE SET NULL,
  CONSTRAINT `student_classes_ibfk_1` FOREIGN KEY (`student_id`) REFERENCES `students` (`id`) ON DELETE CASCADE,
  CONSTRAINT `student_classes_ibfk_2` FOREIGN KEY (`class_id`) REFERENCES `classes` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Data for the table `student_classes` */

/*Table structure for table `student_grades` */

DROP TABLE IF EXISTS `student_grades`;

CREATE TABLE `student_grades` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `student_id` int(11) NOT NULL,
  `class_id` int(11) NOT NULL,
  `assessment_id` int(11) NOT NULL,
  `score` float DEFAULT NULL,
  `percentage` float DEFAULT NULL,
  `letter_grade` varchar(2) DEFAULT NULL,
  `is_released` tinyint(1) DEFAULT 0,
  `released_date` datetime DEFAULT NULL,
  `remarks` varchar(50) DEFAULT NULL,
  `graded_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_student_grades_student_id` (`student_id`),
  KEY `idx_student_grades_class_id` (`class_id`),
  KEY `idx_student_grades_assessment_id` (`assessment_id`),
  KEY `idx_student_grades_letter_grade` (`letter_grade`),
  KEY `idx_student_grades_graded_at` (`graded_at`),
  KEY `idx_student_grades_released` (`is_released`,`released_date`),
  CONSTRAINT `student_grades_ibfk_1` FOREIGN KEY (`student_id`) REFERENCES `students` (`id`) ON DELETE CASCADE,
  CONSTRAINT `student_grades_ibfk_2` FOREIGN KEY (`class_id`) REFERENCES `classes` (`id`) ON DELETE CASCADE,
  CONSTRAINT `student_grades_ibfk_3` FOREIGN KEY (`assessment_id`) REFERENCES `assessments` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Data for the table `student_grades` */

/*Table structure for table `student_scores` */

DROP TABLE IF EXISTS `student_scores`;

CREATE TABLE `student_scores` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `assessment_id` int(11) NOT NULL,
  `student_id` int(11) NOT NULL,
  `score` float NOT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_student_scores_assessment_id` (`assessment_id`),
  KEY `idx_student_scores_student_id` (`student_id`),
  CONSTRAINT `student_scores_fk_assessment_id` FOREIGN KEY (`assessment_id`) REFERENCES `grade_assessments` (`id`) ON DELETE CASCADE,
  CONSTRAINT `student_scores_ibfk_2` FOREIGN KEY (`student_id`) REFERENCES `students` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Data for the table `student_scores` */

/*Table structure for table `students` */

DROP TABLE IF EXISTS `students`;

CREATE TABLE `students` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `personal_info_id` int(11) DEFAULT NULL,
  `course` varchar(10) NOT NULL,
  `track` varchar(50) DEFAULT NULL,
  `year_level` int(11) NOT NULL,
  `section` varchar(10) NOT NULL,
  `approval_status` enum('pending','approved','rejected') DEFAULT 'pending',
  `approved_by` int(11) DEFAULT NULL,
  `approved_at` datetime DEFAULT NULL,
  `rejection_reason` text DEFAULT NULL,
  `id_front_path` varchar(255) DEFAULT NULL,
  `id_back_path` varchar(255) DEFAULT NULL,
  `face_photo_path` varchar(255) DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_students_user_id` (`user_id`),
  KEY `idx_students_personal_info_id` (`personal_info_id`),
  KEY `idx_students_course` (`course`),
  KEY `idx_students_track` (`track`),
  KEY `idx_students_year_level` (`year_level`),
  KEY `idx_students_section` (`section`),
  KEY `idx_students_approval_status` (`approval_status`),
  KEY `fk_students_approved_by` (`approved_by`),
  CONSTRAINT `fk_students_approved_by` FOREIGN KEY (`approved_by`) REFERENCES `users` (`id`) ON DELETE SET NULL,
  CONSTRAINT `students_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `students_ibfk_2` FOREIGN KEY (`personal_info_id`) REFERENCES `personal_info` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Data for the table `students` */

/*Table structure for table `users` */

DROP TABLE IF EXISTS `users`;

CREATE TABLE `users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `school_id` varchar(20) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `role` varchar(20) NOT NULL,
  `account_status` enum('pending','active','suspended','rejected') DEFAULT 'active',
  `created_at` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `school_id` (`school_id`),
  KEY `idx_users_school_id` (`school_id`),
  KEY `idx_users_role` (`role`),
  KEY `idx_users_created_at` (`created_at`),
  KEY `idx_users_account_status` (`account_status`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Data for the table `users` */

insert  into `users`(`id`,`school_id`,`password_hash`,`role`,`account_status`,`created_at`) values 
(1,'admin001','pbkdf2:sha256:600000$TZvfOSZY7KvmbJTf$a2ad3968b576e549855b4e3939db0b5964c9f3f6c8f710f74bacdd215fba6305','admin','active','2025-12-05 22:00:46');

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
