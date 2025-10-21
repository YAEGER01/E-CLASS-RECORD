/*M!999999\- enable the sandbox mode */ 
-- MariaDB dump 10.19-11.6.2-MariaDB, for Win64 (AMD64)
--
-- Host: localhost    Database: e_class_record
-- ------------------------------------------------------
-- Server version	11.6.2-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*M!100616 SET @OLD_NOTE_VERBOSITY=@@NOTE_VERBOSITY, NOTE_VERBOSITY=0 */;

--
-- Table structure for table `assessments_backup`
--

DROP TABLE IF EXISTS `assessments_backup`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `assessments_backup` (
  `id` int(11) NOT NULL DEFAULT 0,
  `category_id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `weight` float DEFAULT NULL,
  `max_score` float NOT NULL,
  `passing_score` float DEFAULT NULL,
  `position` int(11) NOT NULL,
  `description` text DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `assessments_backup`
--

LOCK TABLES `assessments_backup` WRITE;
/*!40000 ALTER TABLE `assessments_backup` DISABLE KEYS */;
/*!40000 ALTER TABLE `assessments_backup` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `class_grading_categories_backup`
--

DROP TABLE IF EXISTS `class_grading_categories_backup`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `class_grading_categories_backup` (
  `id` int(11) NOT NULL DEFAULT 0,
  `template_id` int(11) NOT NULL,
  `name` varchar(50) NOT NULL,
  `weight` float NOT NULL,
  `position` int(11) NOT NULL,
  `created_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `class_grading_categories_backup`
--

LOCK TABLES `class_grading_categories_backup` WRITE;
/*!40000 ALTER TABLE `class_grading_categories_backup` DISABLE KEYS */;
/*!40000 ALTER TABLE `class_grading_categories_backup` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `class_grading_components_backup`
--

DROP TABLE IF EXISTS `class_grading_components_backup`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `class_grading_components_backup` (
  `id` int(11) NOT NULL DEFAULT 0,
  `category_id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `max_score` float NOT NULL,
  `weight` float DEFAULT NULL,
  `position` int(11) NOT NULL,
  `created_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `class_grading_components_backup`
--

LOCK TABLES `class_grading_components_backup` WRITE;
/*!40000 ALTER TABLE `class_grading_components_backup` DISABLE KEYS */;
/*!40000 ALTER TABLE `class_grading_components_backup` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `class_grading_templates_backup`
--

DROP TABLE IF EXISTS `class_grading_templates_backup`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `class_grading_templates_backup` (
  `id` int(11) NOT NULL DEFAULT 0,
  `class_id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `description` text DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT 1,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `class_grading_templates_backup`
--

LOCK TABLES `class_grading_templates_backup` WRITE;
/*!40000 ALTER TABLE `class_grading_templates_backup` DISABLE KEYS */;
/*!40000 ALTER TABLE `class_grading_templates_backup` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `classes`
--

DROP TABLE IF EXISTS `classes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `classes` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `instructor_id` int(11) NOT NULL,
  `year` varchar(4) NOT NULL,
  `semester` varchar(20) NOT NULL,
  `course` varchar(10) NOT NULL,
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
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `classes`
--

LOCK TABLES `classes` WRITE;
/*!40000 ALTER TABLE `classes` DISABLE KEYS */;
INSERT INTO `classes` VALUES
(1,2,'2026','1st sem','BSIT','Networking','3A','M-W-F 8-10AM','c357528a-de10-4280-b102-5e960a567809','798356',NULL,'2025-10-12 21:21:50','2025-10-12 21:21:50'),
(2,2,'2025','2nd sem','BSIS','Networking','2A','M-W-F 8-10AM','1b93d795-24e2-41b0-aa70-d3327e45f158','534985',NULL,'2025-10-12 21:38:42','2025-10-12 21:38:42');
/*!40000 ALTER TABLE `classes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `grade_assessments`
--

DROP TABLE IF EXISTS `grade_assessments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
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
  CONSTRAINT `grade_assessments_ibfk_1` FOREIGN KEY (`subcategory_id`) REFERENCES `grade_subcategories` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `grade_assessments`
--

LOCK TABLES `grade_assessments` WRITE;
/*!40000 ALTER TABLE `grade_assessments` DISABLE KEYS */;
/*!40000 ALTER TABLE `grade_assessments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `grade_categories`
--

DROP TABLE IF EXISTS `grade_categories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
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
  CONSTRAINT `grade_categories_ibfk_1` FOREIGN KEY (`structure_id`) REFERENCES `grade_structures` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `grade_categories`
--

LOCK TABLES `grade_categories` WRITE;
/*!40000 ALTER TABLE `grade_categories` DISABLE KEYS */;
/*!40000 ALTER TABLE `grade_categories` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `grade_structures`
--

DROP TABLE IF EXISTS `grade_structures`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `grade_structures` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `class_id` int(11) NOT NULL,
  `structure_name` varchar(100) NOT NULL,
  `structure_json` text NOT NULL,
  `created_by` int(11) NOT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `is_active` tinyint(1) DEFAULT 1,
  PRIMARY KEY (`id`),
  KEY `idx_grade_structures_class_id` (`class_id`),
  KEY `idx_grade_structures_structure_name` (`structure_name`),
  KEY `idx_grade_structures_created_by` (`created_by`),
  KEY `idx_grade_structures_is_active` (`is_active`),
  CONSTRAINT `grade_structures_ibfk_1` FOREIGN KEY (`class_id`) REFERENCES `classes` (`id`) ON DELETE CASCADE,
  CONSTRAINT `grade_structures_ibfk_2` FOREIGN KEY (`created_by`) REFERENCES `instructors` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `grade_structures`
--

LOCK TABLES `grade_structures` WRITE;
/*!40000 ALTER TABLE `grade_structures` DISABLE KEYS */;
/*!40000 ALTER TABLE `grade_structures` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `grade_subcategories`
--

DROP TABLE IF EXISTS `grade_subcategories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
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
  CONSTRAINT `grade_subcategories_ibfk_1` FOREIGN KEY (`category_id`) REFERENCES `grade_categories` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `grade_subcategories`
--

LOCK TABLES `grade_subcategories` WRITE;
/*!40000 ALTER TABLE `grade_subcategories` DISABLE KEYS */;
/*!40000 ALTER TABLE `grade_subcategories` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `grading_categories_backup`
--

DROP TABLE IF EXISTS `grading_categories_backup`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `grading_categories_backup` (
  `id` int(11) NOT NULL DEFAULT 0,
  `template_id` int(11) NOT NULL,
  `name` varchar(50) NOT NULL,
  `weight` float NOT NULL,
  `position` int(11) NOT NULL,
  `created_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `grading_categories_backup`
--

LOCK TABLES `grading_categories_backup` WRITE;
/*!40000 ALTER TABLE `grading_categories_backup` DISABLE KEYS */;
/*!40000 ALTER TABLE `grading_categories_backup` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `grading_templates_backup`
--

DROP TABLE IF EXISTS `grading_templates_backup`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `grading_templates_backup` (
  `id` int(11) NOT NULL DEFAULT 0,
  `instructor_id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `description` text DEFAULT NULL,
  `is_default` tinyint(1) DEFAULT 0,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `grading_templates_backup`
--

LOCK TABLES `grading_templates_backup` WRITE;
/*!40000 ALTER TABLE `grading_templates_backup` DISABLE KEYS */;
/*!40000 ALTER TABLE `grading_templates_backup` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `instructors`
--

DROP TABLE IF EXISTS `instructors`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
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
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `instructors`
--

LOCK TABLES `instructors` WRITE;
/*!40000 ALTER TABLE `instructors` DISABLE KEYS */;
INSERT INTO `instructors` VALUES
(2,3,2,'Computer Science','NE','CL-002',NULL,'active','2025-10-12 21:21:16','2025-10-14 08:01:20');
/*!40000 ALTER TABLE `instructors` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `personal_info`
--

DROP TABLE IF EXISTS `personal_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
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
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `personal_info`
--

LOCK TABLES `personal_info` WRITE;
/*!40000 ALTER TABLE `personal_info` DISABLE KEYS */;
INSERT INTO `personal_info` VALUES
(2,'Ako','Fred',NULL,'qwieqwiru@gmail.com','1233451234','Bhay namin','1993-12-31','Male','Ako','12903581','2025-10-12 21:21:16','2025-10-12 21:21:16'),
(3,'Student','User',NULL,'23-13439@student.edu',NULL,NULL,NULL,NULL,NULL,NULL,'2025-10-12 21:46:43','2025-10-12 21:46:43');
/*!40000 ALTER TABLE `personal_info` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `student_classes`
--

DROP TABLE IF EXISTS `student_classes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `student_classes` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `student_id` int(11) NOT NULL,
  `class_id` int(11) NOT NULL,
  `joined_at` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_student_class` (`student_id`,`class_id`),
  KEY `idx_student_classes_student_id` (`student_id`),
  KEY `idx_student_classes_class_id` (`class_id`),
  KEY `idx_student_classes_joined_at` (`joined_at`),
  CONSTRAINT `student_classes_ibfk_1` FOREIGN KEY (`student_id`) REFERENCES `students` (`id`) ON DELETE CASCADE,
  CONSTRAINT `student_classes_ibfk_2` FOREIGN KEY (`class_id`) REFERENCES `classes` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `student_classes`
--

LOCK TABLES `student_classes` WRITE;
/*!40000 ALTER TABLE `student_classes` DISABLE KEYS */;
INSERT INTO `student_classes` VALUES
(14,1,1,'2025-10-13 07:45:24');
/*!40000 ALTER TABLE `student_classes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `student_grades`
--

DROP TABLE IF EXISTS `student_grades`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `student_grades` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `student_id` int(11) NOT NULL,
  `class_id` int(11) NOT NULL,
  `assessment_id` int(11) NOT NULL,
  `score` float DEFAULT NULL,
  `percentage` float DEFAULT NULL,
  `letter_grade` varchar(2) DEFAULT NULL,
  `remarks` varchar(50) DEFAULT NULL,
  `graded_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_student_grades_student_id` (`student_id`),
  KEY `idx_student_grades_class_id` (`class_id`),
  KEY `idx_student_grades_assessment_id` (`assessment_id`),
  KEY `idx_student_grades_letter_grade` (`letter_grade`),
  KEY `idx_student_grades_graded_at` (`graded_at`),
  CONSTRAINT `student_grades_ibfk_1` FOREIGN KEY (`student_id`) REFERENCES `students` (`id`) ON DELETE CASCADE,
  CONSTRAINT `student_grades_ibfk_2` FOREIGN KEY (`class_id`) REFERENCES `classes` (`id`) ON DELETE CASCADE,
  CONSTRAINT `student_grades_ibfk_3` FOREIGN KEY (`assessment_id`) REFERENCES `assessments` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `student_grades`
--

LOCK TABLES `student_grades` WRITE;
/*!40000 ALTER TABLE `student_grades` DISABLE KEYS */;
/*!40000 ALTER TABLE `student_grades` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `student_scores`
--

DROP TABLE IF EXISTS `student_scores`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
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
  CONSTRAINT `student_scores_ibfk_1` FOREIGN KEY (`assessment_id`) REFERENCES `assessments` (`id`) ON DELETE CASCADE,
  CONSTRAINT `student_scores_ibfk_2` FOREIGN KEY (`student_id`) REFERENCES `students` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `student_scores`
--

LOCK TABLES `student_scores` WRITE;
/*!40000 ALTER TABLE `student_scores` DISABLE KEYS */;
/*!40000 ALTER TABLE `student_scores` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students`
--

DROP TABLE IF EXISTS `students`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `students` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `personal_info_id` int(11) DEFAULT NULL,
  `course` varchar(10) NOT NULL,
  `track` varchar(50) DEFAULT NULL,
  `year_level` int(11) NOT NULL,
  `section` varchar(10) NOT NULL,
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
  CONSTRAINT `students_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `students_ibfk_2` FOREIGN KEY (`personal_info_id`) REFERENCES `personal_info` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students`
--

LOCK TABLES `students` WRITE;
/*!40000 ALTER TABLE `students` DISABLE KEYS */;
INSERT INTO `students` VALUES
(1,4,3,'BSIT','Networking',3,'A',NULL,NULL,NULL,'2025-10-12 21:46:43');
/*!40000 ALTER TABLE `students` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `school_id` varchar(20) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `role` varchar(20) NOT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `school_id` (`school_id`),
  KEY `idx_users_school_id` (`school_id`),
  KEY `idx_users_role` (`role`),
  KEY `idx_users_created_at` (`created_at`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES
(1,'admin001','scrypt:32768:8:1$ZrV1jWlbTwV7H4EG$5b032f51832e38b8ac4a886f1ec6f848678aa58ef4510208b3ab2ec6d5ac3a76d0155b0bf71e373bac292d002f09ee407fa8796fc7e5bfdc6fe2886439d17319','admin','2025-10-12 21:16:13'),
(3,'CL-002','scrypt:32768:8:1$Mmlr1OOeGnXXnb84$954357e5d3e45643eed2d4a8dc6fb82a53c73cad0e8936ed0cef124bb84d9654fca162ac73077a80c3eb944a06506f4cfde88fe4cbfabaa46fe179da59c4fe2a','instructor','2025-10-12 21:21:16'),
(4,'23-13439','scrypt:32768:8:1$Wg1aTfNlklNg2Kt0$25a82d750d8c5fdb2ba413f2d4b0e92c731c4362c9e96e82be86433c9773b4f45c8f77305808272b638130a809de2554b0801da52297eb98523b98609ea7a0f8','student','2025-10-12 21:46:43');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*M!100616 SET NOTE_VERBOSITY=@OLD_NOTE_VERBOSITY */;

-- Dump completed on 2025-10-14 16:22:02
