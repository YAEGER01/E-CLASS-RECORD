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
-- Table structure for table `audit_logs`
--

DROP TABLE IF EXISTS `audit_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `audit_logs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `admin_id` int(11) NOT NULL,
  `admin_school_id` varchar(20) NOT NULL,
  `action` varchar(100) NOT NULL,
  `resource_type` varchar(50) NOT NULL,
  `resource_id` int(11) DEFAULT NULL,
  `details` text DEFAULT NULL,
  `ip_address` varchar(45) DEFAULT NULL,
  `user_agent` text DEFAULT NULL,
  `timestamp` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_audit_logs_admin_id` (`admin_id`),
  KEY `idx_audit_logs_action` (`action`),
  KEY `idx_audit_logs_resource_type` (`resource_type`),
  KEY `idx_audit_logs_timestamp` (`timestamp`),
  KEY `idx_audit_logs_admin_school_id` (`admin_school_id`),
  CONSTRAINT `audit_logs_ibfk_1` FOREIGN KEY (`admin_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `audit_logs`
--

LOCK TABLES `audit_logs` WRITE;
/*!40000 ALTER TABLE `audit_logs` DISABLE KEYS */;
INSERT INTO `audit_logs` VALUES
(1,1,'admin001','SYSTEM_MIGRATION','database',NULL,'Added audit_logs table for admin action tracking',NULL,NULL,'2025-11-25 02:04:51'),
(2,1,'admin001','GENERATE_REPORT','report',NULL,'Generated user report','127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0','2025-11-25 02:06:25'),
(3,1,'admin001','GENERATE_REPORT','report',NULL,'Generated class report','127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0','2025-11-25 02:06:29'),
(4,1,'admin001','GENERATE_REPORT','report',NULL,'Generated system report','127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0','2025-11-25 02:06:33'),
(5,1,'admin001','GENERATE_REPORT','report',NULL,'Generated system report','127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0','2025-11-25 02:07:42'),
(6,1,'admin001','GENERATE_REPORT','report',NULL,'Generated system report','127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0','2025-11-25 02:11:04');
/*!40000 ALTER TABLE `audit_logs` ENABLE KEYS */;
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
  `class_type` varchar(10) DEFAULT NULL,
  `year` varchar(4) NOT NULL,
  `semester` varchar(20) NOT NULL,
  `course` varchar(10) NOT NULL,
  `subject` varchar(100) NOT NULL,
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
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `classes`
--

LOCK TABLES `classes` WRITE;
/*!40000 ALTER TABLE `classes` DISABLE KEYS */;
INSERT INTO `classes` VALUES
(1,1,'MAJOR','2024','1st sem','BSIT','Intro To Programming desu','Programming','1A','M-W-F 8-10AM','59fd9305-477b-4ba4-a912-4691caf62b39','008448',NULL,'2025-11-16 18:38:36','2025-11-26 11:25:15');
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
  CONSTRAINT `fk_subcategory` FOREIGN KEY (`subcategory_id`) REFERENCES `grade_subcategories` (`id`) ON DELETE CASCADE,
  CONSTRAINT `grade_assessments_ibfk_1` FOREIGN KEY (`subcategory_id`) REFERENCES `grade_subcategories` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `grade_assessments`
--

LOCK TABLES `grade_assessments` WRITE;
/*!40000 ALTER TABLE `grade_assessments` DISABLE KEYS */;
INSERT INTO `grade_assessments` VALUES
(3,1,'Participation 4',NULL,100,NULL,1,NULL,'2025-11-18 21:19:01'),
(4,2,'Assessment 1',NULL,100,NULL,1,NULL,'2025-11-18 22:41:26'),
(5,3,'Assessment 1',NULL,100,NULL,1,NULL,'2025-11-18 22:41:30'),
(6,4,'Quiz 1',NULL,67,NULL,1,NULL,'2025-11-26 19:16:54');
/*!40000 ALTER TABLE `grade_assessments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `grade_calculation_templates`
--

DROP TABLE IF EXISTS `grade_calculation_templates`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `grade_calculation_templates` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `description` text DEFAULT NULL,
  `template_json` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL CHECK (json_valid(`template_json`)),
  `is_default` tinyint(1) DEFAULT 0,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `grade_calculation_templates`
--

LOCK TABLES `grade_calculation_templates` WRITE;
/*!40000 ALTER TABLE `grade_calculation_templates` DISABLE KEYS */;
/*!40000 ALTER TABLE `grade_calculation_templates` ENABLE KEYS */;
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
  CONSTRAINT `fk_structure` FOREIGN KEY (`structure_id`) REFERENCES `grade_structures` (`id`) ON DELETE CASCADE,
  CONSTRAINT `grade_categories_ibfk_1` FOREIGN KEY (`structure_id`) REFERENCES `grade_structures` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `grade_categories`
--

LOCK TABLES `grade_categories` WRITE;
/*!40000 ALTER TABLE `grade_categories` DISABLE KEYS */;
INSERT INTO `grade_categories` VALUES
(1,1,'LABORATORY',100,1,NULL,'2025-11-18 20:57:01'),
(2,1,'LECTURE',100,1,NULL,'2025-11-26 19:16:39');
/*!40000 ALTER TABLE `grade_categories` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `grade_snapshots`
--

DROP TABLE IF EXISTS `grade_snapshots`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
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
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `grade_snapshots`
--

LOCK TABLES `grade_snapshots` WRITE;
/*!40000 ALTER TABLE `grade_snapshots` DISABLE KEYS */;
INSERT INTO `grade_snapshots` VALUES
(1,1,1,'draft','{\"meta\": {\"class_id\": 1, \"structure_version\": null, \"saved_at\": \"2025-11-26T03:42:57.727329Z\"}, \"assessments\": [{\"id\": 3, \"name\": \"Participation 4\", \"max_score\": 100.0, \"category\": \"LABORATORY\", \"subcategory\": \"LAB PARTICIPATION\", \"subweight\": 10.0}, {\"id\": 4, \"name\": \"Assessment 1\", \"max_score\": 100.0, \"category\": \"LABORATORY\", \"subcategory\": \"LAB HOMEWORK\", \"subweight\": 10.0}, {\"id\": 5, \"name\": \"Assessment 1\", \"max_score\": 100.0, \"category\": \"LABORATORY\", \"subcategory\": \"LAB EXERCISE\", \"subweight\": 80.0}], \"students\": [{\"student_id\": 10, \"scores\": [{\"assessment_id\": 3, \"score\": 0.0}, {\"assessment_id\": 4, \"score\": 0.0}, {\"assessment_id\": 5, \"score\": 0.0}], \"computed\": {\"category_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"weighted_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"category_ratings\": {\"LABORATORY\": 0.0}, \"overall_percentage\": 0.0, \"final_grade\": 37.5, \"letter_grade\": \"5.00\", \"remarks\": null}}, {\"student_id\": 30, \"scores\": [{\"assessment_id\": 3, \"score\": 0.0}, {\"assessment_id\": 4, \"score\": 0.0}, {\"assessment_id\": 5, \"score\": 0.0}], \"computed\": {\"category_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"weighted_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"category_ratings\": {\"LABORATORY\": 0.0}, \"overall_percentage\": 0.0, \"final_grade\": 37.5, \"letter_grade\": \"5.00\", \"remarks\": null}}, {\"student_id\": 21, \"scores\": [{\"assessment_id\": 3, \"score\": 0.0}, {\"assessment_id\": 4, \"score\": 0.0}, {\"assessment_id\": 5, \"score\": 0.0}], \"computed\": {\"category_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"weighted_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"category_ratings\": {\"LABORATORY\": 0.0}, \"overall_percentage\": 0.0, \"final_grade\": 37.5, \"letter_grade\": \"5.00\", \"remarks\": null}}, {\"student_id\": 1, \"scores\": [{\"assessment_id\": 3, \"score\": 0.0}, {\"assessment_id\": 4, \"score\": 0.0}, {\"assessment_id\": 5, \"score\": 0.0}], \"computed\": {\"category_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"weighted_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"category_ratings\": {\"LABORATORY\": 0.0}, \"overall_percentage\": 0.0, \"final_grade\": 37.5, \"letter_grade\": \"5.00\", \"remarks\": null}}, {\"student_id\": 23, \"scores\": [{\"assessment_id\": 3, \"score\": 0.0}, {\"assessment_id\": 4, \"score\": 0.0}, {\"assessment_id\": 5, \"score\": 0.0}], \"computed\": {\"category_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"weighted_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"category_ratings\": {\"LABORATORY\": 0.0}, \"overall_percentage\": 0.0, \"final_grade\": 37.5, \"letter_grade\": \"5.00\", \"remarks\": null}}, {\"student_id\": 2, \"scores\": [{\"assessment_id\": 3, \"score\": 0.0}, {\"assessment_id\": 4, \"score\": 0.0}, {\"assessment_id\": 5, \"score\": 0.0}], \"computed\": {\"category_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"weighted_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"category_ratings\": {\"LABORATORY\": 0.0}, \"overall_percentage\": 0.0, \"final_grade\": 37.5, \"letter_grade\": \"5.00\", \"remarks\": null}}, {\"student_id\": 8, \"scores\": [{\"assessment_id\": 3, \"score\": 0.0}, {\"assessment_id\": 4, \"score\": 0.0}, {\"assessment_id\": 5, \"score\": 0.0}], \"computed\": {\"category_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"weighted_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"category_ratings\": {\"LABORATORY\": 0.0}, \"overall_percentage\": 0.0, \"final_grade\": 37.5, \"letter_grade\": \"5.00\", \"remarks\": null}}, {\"student_id\": 28, \"scores\": [{\"assessment_id\": 3, \"score\": 0.0}, {\"assessment_id\": 4, \"score\": 0.0}, {\"assessment_id\": 5, \"score\": 0.0}], \"computed\": {\"category_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"weighted_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"category_ratings\": {\"LABORATORY\": 0.0}, \"overall_percentage\": 0.0, \"final_grade\": 37.5, \"letter_grade\": \"5.00\", \"remarks\": null}}, {\"student_id\": 20, \"scores\": [{\"assessment_id\": 3, \"score\": 0.0}, {\"assessment_id\": 4, \"score\": 0.0}, {\"assessment_id\": 5, \"score\": 0.0}], \"computed\": {\"category_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"weighted_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"category_ratings\": {\"LABORATORY\": 0.0}, \"overall_percentage\": 0.0, \"final_grade\": 37.5, \"letter_grade\": \"5.00\", \"remarks\": null}}, {\"student_id\": 40, \"scores\": [{\"assessment_id\": 3, \"score\": 0.0}, {\"assessment_id\": 4, \"score\": 0.0}, {\"assessment_id\": 5, \"score\": 0.0}], \"computed\": {\"category_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"weighted_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"category_ratings\": {\"LABORATORY\": 0.0}, \"overall_percentage\": 0.0, \"final_grade\": 37.5, \"letter_grade\": \"5.00\", \"remarks\": null}}, {\"student_id\": 26, \"scores\": [{\"assessment_id\": 3, \"score\": 0.0}, {\"assessment_id\": 4, \"score\": 0.0}, {\"assessment_id\": 5, \"score\": 0.0}], \"computed\": {\"category_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"weighted_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"category_ratings\": {\"LABORATORY\": 0.0}, \"overall_percentage\": 0.0, \"final_grade\": 37.5, \"letter_grade\": \"5.00\", \"remarks\": null}}, {\"student_id\": 7, \"scores\": [{\"assessment_id\": 3, \"score\": 0.0}, {\"assessment_id\": 4, \"score\": 0.0}, {\"assessment_id\": 5, \"score\": 0.0}], \"computed\": {\"category_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"weighted_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"category_ratings\": {\"LABORATORY\": 0.0}, \"overall_percentage\": 0.0, \"final_grade\": 37.5, \"letter_grade\": \"5.00\", \"remarks\": null}}, {\"student_id\": 14, \"scores\": [{\"assessment_id\": 3, \"score\": 0.0}, {\"assessment_id\": 4, \"score\": 0.0}, {\"assessment_id\": 5, \"score\": 0.0}], \"computed\": {\"category_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"weighted_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"category_ratings\": {\"LABORATORY\": 0.0}, \"overall_percentage\": 0.0, \"final_grade\": 37.5, \"letter_grade\": \"5.00\", \"remarks\": null}}, {\"student_id\": 34, \"scores\": [{\"assessment_id\": 3, \"score\": 0.0}, {\"assessment_id\": 4, \"score\": 0.0}, {\"assessment_id\": 5, \"score\": 0.0}], \"computed\": {\"category_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"weighted_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"category_ratings\": {\"LABORATORY\": 0.0}, \"overall_percentage\": 0.0, \"final_grade\": 37.5, \"letter_grade\": \"5.00\", \"remarks\": null}}, {\"student_id\": 36, \"scores\": [{\"assessment_id\": 3, \"score\": 0.0}, {\"assessment_id\": 4, \"score\": 0.0}, {\"assessment_id\": 5, \"score\": 0.0}], \"computed\": {\"category_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"weighted_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"category_ratings\": {\"LABORATORY\": 0.0}, \"overall_percentage\": 0.0, \"final_grade\": 37.5, \"letter_grade\": \"5.00\", \"remarks\": null}}, {\"student_id\": 16, \"scores\": [{\"assessment_id\": 3, \"score\": 0.0}, {\"assessment_id\": 4, \"score\": 0.0}, {\"assessment_id\": 5, \"score\": 0.0}], \"computed\": {\"category_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"weighted_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"category_ratings\": {\"LABORATORY\": 0.0}, \"overall_percentage\": 0.0, \"final_grade\": 37.5, \"letter_grade\": \"5.00\", \"remarks\": null}}, {\"student_id\": 5, \"scores\": [{\"assessment_id\": 3, \"score\": 0.0}, {\"assessment_id\": 4, \"score\": 0.0}, {\"assessment_id\": 5, \"score\": 0.0}], \"computed\": {\"category_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"weighted_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"category_ratings\": {\"LABORATORY\": 0.0}, \"overall_percentage\": 0.0, \"final_grade\": 37.5, \"letter_grade\": \"5.00\", \"remarks\": null}}, {\"student_id\": 27, \"scores\": [{\"assessment_id\": 3, \"score\": 0.0}, {\"assessment_id\": 4, \"score\": 0.0}, {\"assessment_id\": 5, \"score\": 0.0}], \"computed\": {\"category_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"weighted_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"category_ratings\": {\"LABORATORY\": 0.0}, \"overall_percentage\": 0.0, \"final_grade\": 37.5, \"letter_grade\": \"5.00\", \"remarks\": null}}, {\"student_id\": 35, \"scores\": [{\"assessment_id\": 3, \"score\": 0.0}, {\"assessment_id\": 4, \"score\": 0.0}, {\"assessment_id\": 5, \"score\": 0.0}], \"computed\": {\"category_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"weighted_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"category_ratings\": {\"LABORATORY\": 0.0}, \"overall_percentage\": 0.0, \"final_grade\": 37.5, \"letter_grade\": \"5.00\", \"remarks\": null}}, {\"student_id\": 15, \"scores\": [{\"assessment_id\": 3, \"score\": 0.0}, {\"assessment_id\": 4, \"score\": 0.0}, {\"assessment_id\": 5, \"score\": 0.0}], \"computed\": {\"category_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"weighted_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"category_ratings\": {\"LABORATORY\": 0.0}, \"overall_percentage\": 0.0, \"final_grade\": 37.5, \"letter_grade\": \"5.00\", \"remarks\": null}}, {\"student_id\": 25, \"scores\": [{\"assessment_id\": 3, \"score\": 0.0}, {\"assessment_id\": 4, \"score\": 0.0}, {\"assessment_id\": 5, \"score\": 0.0}], \"computed\": {\"category_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"weighted_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"category_ratings\": {\"LABORATORY\": 0.0}, \"overall_percentage\": 0.0, \"final_grade\": 37.5, \"letter_grade\": \"5.00\", \"remarks\": null}}, {\"student_id\": 6, \"scores\": [{\"assessment_id\": 3, \"score\": 0.0}, {\"assessment_id\": 4, \"score\": 0.0}, {\"assessment_id\": 5, \"score\": 0.0}], \"computed\": {\"category_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"weighted_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"category_ratings\": {\"LABORATORY\": 0.0}, \"overall_percentage\": 0.0, \"final_grade\": 37.5, \"letter_grade\": \"5.00\", \"remarks\": null}}, {\"student_id\": 22, \"scores\": [{\"assessment_id\": 3, \"score\": 0.0}, {\"assessment_id\": 4, \"score\": 0.0}, {\"assessment_id\": 5, \"score\": 0.0}], \"computed\": {\"category_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"weighted_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"category_ratings\": {\"LABORATORY\": 0.0}, \"overall_percentage\": 0.0, \"final_grade\": 37.5, \"letter_grade\": \"5.00\", \"remarks\": null}}, {\"student_id\": 13, \"scores\": [{\"assessment_id\": 3, \"score\": 0.0}, {\"assessment_id\": 4, \"score\": 0.0}, {\"assessment_id\": 5, \"score\": 0.0}], \"computed\": {\"category_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"weighted_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"category_ratings\": {\"LABORATORY\": 0.0}, \"overall_percentage\": 0.0, \"final_grade\": 37.5, \"letter_grade\": \"5.00\", \"remarks\": null}}, {\"student_id\": 33, \"scores\": [{\"assessment_id\": 3, \"score\": 0.0}, {\"assessment_id\": 4, \"score\": 0.0}, {\"assessment_id\": 5, \"score\": 0.0}], \"computed\": {\"category_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"weighted_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"category_ratings\": {\"LABORATORY\": 0.0}, \"overall_percentage\": 0.0, \"final_grade\": 37.5, \"letter_grade\": \"5.00\", \"remarks\": null}}, {\"student_id\": 17, \"scores\": [{\"assessment_id\": 3, \"score\": 0.0}, {\"assessment_id\": 4, \"score\": 0.0}, {\"assessment_id\": 5, \"score\": 0.0}], \"computed\": {\"category_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"weighted_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"category_ratings\": {\"LABORATORY\": 0.0}, \"overall_percentage\": 0.0, \"final_grade\": 37.5, \"letter_grade\": \"5.00\", \"remarks\": null}}, {\"student_id\": 37, \"scores\": [{\"assessment_id\": 3, \"score\": 0.0}, {\"assessment_id\": 4, \"score\": 0.0}, {\"assessment_id\": 5, \"score\": 0.0}], \"computed\": {\"category_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"weighted_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"category_ratings\": {\"LABORATORY\": 0.0}, \"overall_percentage\": 0.0, \"final_grade\": 37.5, \"letter_grade\": \"5.00\", \"remarks\": null}}, {\"student_id\": 3, \"scores\": [{\"assessment_id\": 3, \"score\": 0.0}, {\"assessment_id\": 4, \"score\": 0.0}, {\"assessment_id\": 5, \"score\": 0.0}], \"computed\": {\"category_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"weighted_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"category_ratings\": {\"LABORATORY\": 0.0}, \"overall_percentage\": 0.0, \"final_grade\": 37.5, \"letter_grade\": \"5.00\", \"remarks\": null}}, {\"student_id\": 24, \"scores\": [{\"assessment_id\": 3, \"score\": 0.0}, {\"assessment_id\": 4, \"score\": 0.0}, {\"assessment_id\": 5, \"score\": 0.0}], \"computed\": {\"category_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"weighted_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"category_ratings\": {\"LABORATORY\": 0.0}, \"overall_percentage\": 0.0, \"final_grade\": 37.5, \"letter_grade\": \"5.00\", \"remarks\": null}}, {\"student_id\": 4, \"scores\": [{\"assessment_id\": 3, \"score\": 0.0}, {\"assessment_id\": 4, \"score\": 0.0}, {\"assessment_id\": 5, \"score\": 0.0}], \"computed\": {\"category_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"weighted_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"category_ratings\": {\"LABORATORY\": 0.0}, \"overall_percentage\": 0.0, \"final_grade\": 37.5, \"letter_grade\": \"5.00\", \"remarks\": null}}, {\"student_id\": 12, \"scores\": [{\"assessment_id\": 3, \"score\": 0.0}, {\"assessment_id\": 4, \"score\": 0.0}, {\"assessment_id\": 5, \"score\": 0.0}], \"computed\": {\"category_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"weighted_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"category_ratings\": {\"LABORATORY\": 0.0}, \"overall_percentage\": 0.0, \"final_grade\": 37.5, \"letter_grade\": \"5.00\", \"remarks\": null}}, {\"student_id\": 32, \"scores\": [{\"assessment_id\": 3, \"score\": 0.0}, {\"assessment_id\": 4, \"score\": 0.0}, {\"assessment_id\": 5, \"score\": 0.0}], \"computed\": {\"category_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"weighted_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"category_ratings\": {\"LABORATORY\": 0.0}, \"overall_percentage\": 0.0, \"final_grade\": 37.5, \"letter_grade\": \"5.00\", \"remarks\": null}}, {\"student_id\": 11, \"scores\": [{\"assessment_id\": 3, \"score\": 0.0}, {\"assessment_id\": 4, \"score\": 0.0}, {\"assessment_id\": 5, \"score\": 0.0}], \"computed\": {\"category_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"weighted_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"category_ratings\": {\"LABORATORY\": 0.0}, \"overall_percentage\": 0.0, \"final_grade\": 37.5, \"letter_grade\": \"5.00\", \"remarks\": null}}, {\"student_id\": 31, \"scores\": [{\"assessment_id\": 3, \"score\": 0.0}, {\"assessment_id\": 4, \"score\": 0.0}, {\"assessment_id\": 5, \"score\": 0.0}], \"computed\": {\"category_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"weighted_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"category_ratings\": {\"LABORATORY\": 0.0}, \"overall_percentage\": 0.0, \"final_grade\": 37.5, \"letter_grade\": \"5.00\", \"remarks\": null}}, {\"student_id\": 18, \"scores\": [{\"assessment_id\": 3, \"score\": 0.0}, {\"assessment_id\": 4, \"score\": 0.0}, {\"assessment_id\": 5, \"score\": 0.0}], \"computed\": {\"category_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"weighted_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"category_ratings\": {\"LABORATORY\": 0.0}, \"overall_percentage\": 0.0, \"final_grade\": 37.5, \"letter_grade\": \"5.00\", \"remarks\": null}}, {\"student_id\": 38, \"scores\": [{\"assessment_id\": 3, \"score\": 0.0}, {\"assessment_id\": 4, \"score\": 0.0}, {\"assessment_id\": 5, \"score\": 0.0}], \"computed\": {\"category_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"weighted_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"category_ratings\": {\"LABORATORY\": 0.0}, \"overall_percentage\": 0.0, \"final_grade\": 37.5, \"letter_grade\": \"5.00\", \"remarks\": null}}, {\"student_id\": 39, \"scores\": [{\"assessment_id\": 3, \"score\": 0.0}, {\"assessment_id\": 4, \"score\": 0.0}, {\"assessment_id\": 5, \"score\": 0.0}], \"computed\": {\"category_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"weighted_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"category_ratings\": {\"LABORATORY\": 0.0}, \"overall_percentage\": 0.0, \"final_grade\": 37.5, \"letter_grade\": \"5.00\", \"remarks\": null}}, {\"student_id\": 19, \"scores\": [{\"assessment_id\": 3, \"score\": 0.0}, {\"assessment_id\": 4, \"score\": 0.0}, {\"assessment_id\": 5, \"score\": 0.0}], \"computed\": {\"category_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"weighted_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"category_ratings\": {\"LABORATORY\": 0.0}, \"overall_percentage\": 0.0, \"final_grade\": 37.5, \"letter_grade\": \"5.00\", \"remarks\": null}}, {\"student_id\": 29, \"scores\": [{\"assessment_id\": 3, \"score\": 0.0}, {\"assessment_id\": 4, \"score\": 0.0}, {\"assessment_id\": 5, \"score\": 0.0}], \"computed\": {\"category_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"weighted_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"category_ratings\": {\"LABORATORY\": 0.0}, \"overall_percentage\": 0.0, \"final_grade\": 37.5, \"letter_grade\": \"5.00\", \"remarks\": null}}, {\"student_id\": 9, \"scores\": [{\"assessment_id\": 3, \"score\": 0.0}, {\"assessment_id\": 4, \"score\": 0.0}, {\"assessment_id\": 5, \"score\": 0.0}], \"computed\": {\"category_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"weighted_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"category_ratings\": {\"LABORATORY\": 0.0}, \"overall_percentage\": 0.0, \"final_grade\": 37.5, \"letter_grade\": \"5.00\", \"remarks\": null}}, {\"student_id\": 41, \"scores\": [{\"assessment_id\": 3, \"score\": 100.0}, {\"assessment_id\": 4, \"score\": 100.0}, {\"assessment_id\": 5, \"score\": 100.0}], \"computed\": {\"category_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 100.0, \"LAB HOMEWORK\": 100.0, \"LAB EXERCISE\": 100.0}}, \"weighted_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 10.0, \"LAB HOMEWORK\": 10.0, \"LAB EXERCISE\": 80.0}}, \"category_ratings\": {\"LABORATORY\": 100.0}, \"overall_percentage\": 40.0, \"final_grade\": 62.5, \"letter_grade\": \"5.00\", \"remarks\": null}}]}',2,'2025-11-26 11:42:57',NULL);
/*!40000 ALTER TABLE `grade_snapshots` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `grade_structure_history`
--

DROP TABLE IF EXISTS `grade_structure_history`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
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
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `grade_structure_history`
--

LOCK TABLES `grade_structure_history` WRITE;
/*!40000 ALTER TABLE `grade_structure_history` DISABLE KEYS */;
/*!40000 ALTER TABLE `grade_structure_history` ENABLE KEYS */;
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
  `version` int(11) NOT NULL DEFAULT 1,
  PRIMARY KEY (`id`),
  KEY `idx_grade_structures_class_id` (`class_id`),
  KEY `idx_grade_structures_structure_name` (`structure_name`),
  KEY `idx_grade_structures_created_by` (`created_by`),
  KEY `idx_grade_structures_is_active` (`is_active`),
  CONSTRAINT `grade_structures_ibfk_1` FOREIGN KEY (`class_id`) REFERENCES `classes` (`id`) ON DELETE CASCADE,
  CONSTRAINT `grade_structures_ibfk_2` FOREIGN KEY (`created_by`) REFERENCES `instructors` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `grade_structures`
--

LOCK TABLES `grade_structures` WRITE;
/*!40000 ALTER TABLE `grade_structures` DISABLE KEYS */;
INSERT INTO `grade_structures` VALUES
(1,1,'TESTINGS','{\"LABORATORY\": [{\"name\": \"LAB PARTICIPATION\", \"weight\": 10, \"assessments\": []}, {\"name\": \"LAB HOMEWORK\", \"weight\": 10, \"assessments\": []}, {\"name\": \"LAB EXERCISE\", \"weight\": 80, \"assessments\": []}], \"LECTURE\": [{\"name\": \"QUIZ\", \"weight\": 100, \"assessments\": []}]}',1,'2025-11-18 20:48:32','2025-11-26 19:16:31',1,1);
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
  CONSTRAINT `fk_category` FOREIGN KEY (`category_id`) REFERENCES `grade_categories` (`id`) ON DELETE CASCADE,
  CONSTRAINT `grade_subcategories_ibfk_1` FOREIGN KEY (`category_id`) REFERENCES `grade_categories` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `grade_subcategories`
--

LOCK TABLES `grade_subcategories` WRITE;
/*!40000 ALTER TABLE `grade_subcategories` DISABLE KEYS */;
INSERT INTO `grade_subcategories` VALUES
(1,1,'LAB PARTICIPATION',10,0,NULL,1,NULL,'2025-11-18 20:57:01'),
(2,1,'LAB HOMEWORK',10,0,NULL,2,NULL,'2025-11-18 20:57:01'),
(3,1,'LAB EXERCISE',80,0,NULL,3,NULL,'2025-11-18 20:57:01'),
(4,2,'QUIZ',100,0,NULL,1,NULL,'2025-11-26 19:16:39');
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
(1,2,1,'Information Technology','NETWORK','INS-007',NULL,'active','2025-11-16 18:34:41','2025-11-16 18:34:41'),
(2,3,2,'English',NULL,'INS-009',NULL,'active','2025-11-16 18:37:27','2025-11-16 18:37:27');
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
) ENGINE=InnoDB AUTO_INCREMENT=44 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `personal_info`
--

LOCK TABLES `personal_info` WRITE;
/*!40000 ALTER TABLE `personal_info` DISABLE KEYS */;
INSERT INTO `personal_info` VALUES
(1,'Frederick','Madayag',NULL,'frederick.madayag_cyn@isu.edu.ph','09277102690',NULL,'1999-03-03','Male','sdfdghfg','09277102690','2025-11-16 18:34:41','2025-11-16 18:34:41'),
(2,'AKOooooooo\\','DOEEE',NULL,'joan@gmail.com','0982354238',NULL,'2000-02-03','Male','AKOooooooo','092222254','2025-11-16 18:37:27','2025-11-16 18:37:27'),
(3,'Juan','Dela Cruz','Santos','juan.delacruz@isu.edu.ph','09171234561',NULL,'2004-05-15','Male','Maria Dela Cruz','09179876543','2025-11-18 20:54:05','2025-11-18 20:54:05'),
(4,'Maria','Garcia','Reyes','maria.garcia@isu.edu.ph','09171234562',NULL,'2005-08-22','Female','Jose Garcia','09179876544','2025-11-18 20:54:05','2025-11-18 20:54:05'),
(5,'Jose','Reyes','Lim','jose.reyes@isu.edu.ph','09171234563',NULL,'2004-11-30','Male','Ana Reyes','09179876545','2025-11-18 20:54:05','2025-11-18 20:54:05'),
(6,'Anna','Santos','Tan','anna.santos@isu.edu.ph','09171234564',NULL,'2005-03-18','Female','Pedro Santos','09179876546','2025-11-18 20:54:05','2025-11-18 20:54:05'),
(7,'Carlos','Lopez','Ong','carlos.lopez@isu.edu.ph','09171234565',NULL,'2004-07-09','Male','Luz Lopez','09179876547','2025-11-18 20:54:05','2025-11-18 20:54:05'),
(8,'Sofia','Martinez','Chua','sofia.martinez@isu.edu.ph','09171234566',NULL,'2005-01-12','Female','Miguel Martinez','09179876548','2025-11-18 20:54:05','2025-11-18 20:54:05'),
(9,'Miguel','Hernandez','Sy','miguel.hernandez@isu.edu.ph','09171234567',NULL,'2004-09-25','Male','Carmen Hernandez','09179876549','2025-11-18 20:54:05','2025-11-18 20:54:05'),
(10,'Isabella','Gonzalez','Go','isabella.gonzalez@isu.edu.ph','09171234568',NULL,'2005-04-05','Female','Luis Gonzalez','09179876550','2025-11-18 20:54:05','2025-11-18 20:54:05'),
(11,'Liam','Wilson','Uy','liam.wilson@isu.edu.ph','09171234569',NULL,'2004-12-01','Male','Emma Wilson','09179876551','2025-11-18 20:54:05','2025-11-18 20:54:05'),
(12,'Olivia','Anderson','Lim','olivia.anderson@isu.edu.ph','09171234570',NULL,'2005-06-17','Female','Noah Anderson','09179876552','2025-11-18 20:54:05','2025-11-18 20:54:05'),
(13,'Noah','Thomas','Tan','noah.thomas@isu.edu.ph','09171234571',NULL,'2004-02-28','Male','Sophia Thomas','09179876553','2025-11-18 20:54:05','2025-11-18 20:54:05'),
(14,'Emma','Taylor','Sy','emma.taylor@isu.edu.ph','09171234572',NULL,'2005-10-10','Female','Jackson Taylor','09179876554','2025-11-18 20:54:05','2025-11-18 20:54:05'),
(15,'James','Moore','Chua','james.moore@isu.edu.ph','09171234573',NULL,'2004-08-14','Male','Ava Moore','09179876555','2025-11-18 20:54:05','2025-11-18 20:54:05'),
(16,'Ava','Jackson','Ong','ava.jackson@isu.edu.ph','09171234574',NULL,'2005-05-20','Female','William Jackson','09179876556','2025-11-18 20:54:05','2025-11-18 20:54:05'),
(17,'William','Martin','Go','william.martin@isu.edu.ph','09171234575',NULL,'2004-03-03','Male','Isabella Martin','09179876557','2025-11-18 20:54:05','2025-11-18 20:54:05'),
(18,'Sophia','Lee','Uy','sophia.lee@isu.edu.ph','09171234576',NULL,'2005-07-07','Female','Benjamin Lee','09179876558','2025-11-18 20:54:05','2025-11-18 20:54:05'),
(19,'Benjamin','Perez','Lim','benjamin.perez@isu.edu.ph','09171234577',NULL,'2004-10-21','Male','Charlotte Perez','09179876559','2025-11-18 20:54:05','2025-11-18 20:54:05'),
(20,'Charlotte','Thompson','Tan','charlotte.thompson@isu.edu.ph','09171234578',NULL,'2005-02-14','Female','Lucas Thompson','09179876560','2025-11-18 20:54:05','2025-11-18 20:54:05'),
(21,'Lucas','White','Sy','lucas.white@isu.edu.ph','09171234579',NULL,'2004-06-30','Male','Amelia White','09179876561','2025-11-18 20:54:05','2025-11-18 20:54:05'),
(22,'Amelia','Harris','Chua','amelia.harris@isu.edu.ph','09171234580',NULL,'2005-09-11','Female','Henry Harris','09179876562','2025-11-18 20:54:05','2025-11-18 20:54:05'),
(23,'Elijah','Davis','Tan','20240021@isu.edu.ph','09171234581',NULL,'2004-01-19','Male','Harper Davis','09179876563','2025-11-18 20:58:53','2025-11-18 20:58:53'),
(24,'Harper','Miller','Sy','20240022@isu.edu.ph','09171234582',NULL,'2005-11-05','Female','Elijah Miller','09179876564','2025-11-18 20:58:53','2025-11-18 20:58:53'),
(25,'Evelyn','Garcia','Lim','20240023@isu.edu.ph','09171234583',NULL,'2004-07-22','Female','Mateo Garcia','09179876565','2025-11-18 20:58:53','2025-11-18 20:58:53'),
(26,'Mateo','Rodriguez','Chua','20240024@isu.edu.ph','09171234584',NULL,'2005-04-08','Male','Elena Rodriguez','09179876566','2025-11-18 20:58:53','2025-11-18 20:58:53'),
(27,'Luna','Martinez','Go','20240025@isu.edu.ph','09171234585',NULL,'2004-09-30','Female','Diego Martinez','09179876567','2025-11-18 20:58:53','2025-11-18 20:58:53'),
(28,'Diego','Hernandez','Uy','20240026@isu.edu.ph','09171234586',NULL,'2005-02-11','Male','Valentina Hernandez','09179876568','2025-11-18 20:58:53','2025-11-18 20:58:53'),
(29,'Valentina','Lopez','Ong','20240027@isu.edu.ph','09171234587',NULL,'2004-12-27','Female','Santiago Lopez','09179876569','2025-11-18 20:58:53','2025-11-18 20:58:53'),
(30,'Santiago','Gonzalez','Tan','20240028@isu.edu.ph','09171234588',NULL,'2005-08-03','Male','Camila Gonzalez','09179876570','2025-11-18 20:58:53','2025-11-18 20:58:53'),
(31,'Camila','Wilson','Sy','20240029@isu.edu.ph','09171234589',NULL,'2004-05-26','Female','Sebastian Wilson','09179876571','2025-11-18 20:58:53','2025-11-18 20:58:53'),
(32,'Sebastian','Anderson','Lim','20240030@isu.edu.ph','09171234590',NULL,'2005-03-14','Male','Zoe Anderson','09179876572','2025-11-18 20:58:53','2025-11-18 20:58:53'),
(33,'Zoe','Thomas','Chua','20240031@isu.edu.ph','09171234591',NULL,'2004-10-17','Female','Leo Thomas','09179876573','2025-11-18 20:58:53','2025-11-18 20:58:53'),
(34,'Leo','Taylor','Go','20240032@isu.edu.ph','09171234592',NULL,'2005-06-29','Male','Mila Taylor','09179876574','2025-11-18 20:58:53','2025-11-18 20:58:53'),
(35,'Mila','Moore','Uy','20240033@isu.edu.ph','09171234593',NULL,'2004-04-04','Female','Jack Moore','09179876575','2025-11-18 20:58:53','2025-11-18 20:58:53'),
(36,'Jack','Jackson','Ong','20240034@isu.edu.ph','09171234594',NULL,'2005-01-23','Male','Ellie Jackson','09179876576','2025-11-18 20:58:53','2025-11-18 20:58:53'),
(37,'Ellie','Martin','Tan','20240035@isu.edu.ph','09171234595',NULL,'2004-11-08','Female','Ezra Martin','09179876577','2025-11-18 20:58:53','2025-11-18 20:58:53'),
(38,'Ezra','Lee','Sy','20240036@isu.edu.ph','09171234596',NULL,'2005-07-15','Male','Nora Lee','09179876578','2025-11-18 20:58:53','2025-11-18 20:58:53'),
(39,'Nora','Perez','Lim','20240037@isu.edu.ph','09171234597',NULL,'2004-02-20','Female','Oliver Perez','09179876579','2025-11-18 20:58:53','2025-11-18 20:58:53'),
(40,'Oliver','Thompson','Chua','20240038@isu.edu.ph','09171234598',NULL,'2005-09-02','Male','Aria Thompson','09179876580','2025-11-18 20:58:53','2025-11-18 20:58:53'),
(41,'Aria','White','Go','20240039@isu.edu.ph','09171234599',NULL,'2004-06-11','Female','Luca White','09179876581','2025-11-18 20:58:53','2025-11-18 20:58:53'),
(42,'Luca','Harris','Uy','20240040@isu.edu.ph','09171234600',NULL,'2005-12-05','Male','Maya Harris','09179876582','2025-11-18 20:58:53','2025-11-18 20:58:53'),
(43,'Student','BISAYA','','23-13439@student.edu','','',NULL,'','','','2025-11-19 19:06:03','2025-11-25 00:30:26');
/*!40000 ALTER TABLE `personal_info` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `professor_calculation_overrides`
--

DROP TABLE IF EXISTS `professor_calculation_overrides`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
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
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `professor_calculation_overrides`
--

LOCK TABLES `professor_calculation_overrides` WRITE;
/*!40000 ALTER TABLE `professor_calculation_overrides` DISABLE KEYS */;
/*!40000 ALTER TABLE `professor_calculation_overrides` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `released_grades`
--

DROP TABLE IF EXISTS `released_grades`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `released_grades` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `class_id` int(11) NOT NULL,
  `snapshot_id` int(11) NOT NULL,
  `student_id` int(11) NOT NULL,
  `student_school_id` varchar(20) DEFAULT NULL,
  `student_name` varchar(255) DEFAULT NULL,
  `final_grade` decimal(5,2) DEFAULT NULL,
  `equivalent` varchar(10) DEFAULT NULL,
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
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `released_grades`
--

LOCK TABLES `released_grades` WRITE;
/*!40000 ALTER TABLE `released_grades` DISABLE KEYS */;
INSERT INTO `released_grades` VALUES
(1,1,1,11,'20240011','Thomas, Noah Tan',37.62,'5.00',0.200,'released','{\"student_id\": 11, \"scores\": [{\"assessment_id\": 3, \"score\": 5.0}], \"final_grade\": 37.62, \"equivalent\": \"5.00\", \"computed\": {\"category_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 5.0, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"weighted_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 0.5, \"LAB HOMEWORK\": 0.0, \"LAB EXERCISE\": 0.0}}, \"category_ratings\": {\"LABORATORY\": 0.5}, \"overall_percentage\": 0.2, \"final_grade\": 37.62, \"letter_grade\": \"5.00\", \"remarks\": null}}',2,'2025-11-19 00:14:30','2025-11-19 00:14:30','2025-11-19 00:14:30'),
(2,1,1,10,'20240010','Anderson, Olivia Lim',NULL,'N/A',NULL,'hidden','{\"student_id\": 10}',2,NULL,'2025-11-19 00:19:06','2025-11-26 18:59:32'),
(3,1,1,30,'20240030','Anderson, Sebastian Lim',NULL,'N/A',NULL,'hidden','{\"student_id\": 30}',2,NULL,'2025-11-19 00:23:06','2025-11-26 19:11:44'),
(4,1,1,21,'20240021','Davis, Elijah Tan',NULL,'N/A',NULL,'released','{\"student_id\": 21}',2,'2025-11-19 00:14:30','2025-11-19 18:53:37','2025-11-19 18:53:37'),
(5,1,2,41,'23-13439','User, Student',62.50,'5.00',40.000,'released','{\"student_id\": 41, \"scores\": [{\"assessment_id\": 3, \"score\": 100.0}, {\"assessment_id\": 4, \"score\": 100.0}, {\"assessment_id\": 5, \"score\": 100.0}], \"final_grade\": 62.5, \"equivalent\": \"5.00\", \"computed\": {\"category_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 100.0, \"LAB HOMEWORK\": 100.0, \"LAB EXERCISE\": 100.0}}, \"weighted_totals\": {\"LABORATORY\": {\"LAB PARTICIPATION\": 10.0, \"LAB HOMEWORK\": 10.0, \"LAB EXERCISE\": 80.0}}, \"category_ratings\": {\"LABORATORY\": 100.0}, \"overall_percentage\": 40.0, \"final_grade\": 62.5, \"letter_grade\": \"5.00\", \"remarks\": null}}',2,'2025-11-19 22:32:55','2025-11-19 22:32:55','2025-11-19 22:32:55');
/*!40000 ALTER TABLE `released_grades` ENABLE KEYS */;
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
) ENGINE=InnoDB AUTO_INCREMENT=42 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `student_classes`
--

LOCK TABLES `student_classes` WRITE;
/*!40000 ALTER TABLE `student_classes` DISABLE KEYS */;
INSERT INTO `student_classes` VALUES
(1,1,1,'2025-11-18 20:54:06'),
(2,2,1,'2025-11-18 20:54:06'),
(3,3,1,'2025-11-18 20:54:06'),
(4,4,1,'2025-11-18 20:54:06'),
(5,5,1,'2025-11-18 20:54:06'),
(6,6,1,'2025-11-18 20:54:06'),
(7,7,1,'2025-11-18 20:54:06'),
(8,8,1,'2025-11-18 20:54:06'),
(9,9,1,'2025-11-18 20:54:06'),
(10,10,1,'2025-11-18 20:54:06'),
(11,11,1,'2025-11-18 20:54:06'),
(12,12,1,'2025-11-18 20:54:06'),
(13,13,1,'2025-11-18 20:54:06'),
(14,14,1,'2025-11-18 20:54:06'),
(15,15,1,'2025-11-18 20:54:06'),
(16,16,1,'2025-11-18 20:54:06'),
(17,17,1,'2025-11-18 20:54:06'),
(18,18,1,'2025-11-18 20:54:06'),
(19,19,1,'2025-11-18 20:54:06'),
(20,20,1,'2025-11-18 20:54:06'),
(21,21,1,'2025-11-18 20:58:54'),
(22,22,1,'2025-11-18 20:58:54'),
(23,23,1,'2025-11-18 20:58:54'),
(24,24,1,'2025-11-18 20:58:54'),
(25,25,1,'2025-11-18 20:58:54'),
(26,26,1,'2025-11-18 20:58:54'),
(27,27,1,'2025-11-18 20:58:54'),
(28,28,1,'2025-11-18 20:58:54'),
(29,29,1,'2025-11-18 20:58:54'),
(30,30,1,'2025-11-18 20:58:54'),
(31,31,1,'2025-11-18 20:58:54'),
(32,32,1,'2025-11-18 20:58:54'),
(33,33,1,'2025-11-18 20:58:54'),
(34,34,1,'2025-11-18 20:58:54'),
(35,35,1,'2025-11-18 20:58:54'),
(36,36,1,'2025-11-18 20:58:54'),
(37,37,1,'2025-11-18 20:58:54'),
(38,38,1,'2025-11-18 20:58:54'),
(39,39,1,'2025-11-18 20:58:54'),
(40,40,1,'2025-11-18 20:58:54'),
(41,41,1,'2025-11-19 21:40:25');
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
  CONSTRAINT `student_scores_fk_assessment_id` FOREIGN KEY (`assessment_id`) REFERENCES `grade_assessments` (`id`) ON DELETE CASCADE,
  CONSTRAINT `student_scores_ibfk_2` FOREIGN KEY (`student_id`) REFERENCES `students` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=629 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `student_scores`
--

LOCK TABLES `student_scores` WRITE;
/*!40000 ALTER TABLE `student_scores` DISABLE KEYS */;
INSERT INTO `student_scores` VALUES
(503,3,10,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(504,4,10,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(505,5,10,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(506,3,30,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(507,4,30,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(508,5,30,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(512,3,21,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(513,4,21,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(514,5,21,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(515,3,1,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(516,4,1,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(517,5,1,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(518,3,23,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(519,4,23,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(520,5,23,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(521,3,2,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(522,4,2,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(523,5,2,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(524,3,8,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(525,4,8,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(526,5,8,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(527,3,28,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(528,4,28,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(529,5,28,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(530,3,20,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(531,4,20,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(532,5,20,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(533,3,40,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(534,4,40,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(535,5,40,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(536,3,26,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(537,4,26,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(538,5,26,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(539,3,7,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(540,4,7,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(541,5,7,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(542,3,14,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(543,4,14,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(544,5,14,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(545,3,34,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(546,4,34,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(547,5,34,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(548,3,36,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(549,4,36,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(550,5,36,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(551,3,16,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(552,4,16,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(553,5,16,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(554,3,5,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(555,4,5,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(556,5,5,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(557,3,27,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(558,4,27,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(559,5,27,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(560,3,35,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(561,4,35,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(562,5,35,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(563,3,15,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(564,4,15,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(565,5,15,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(566,3,25,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(567,4,25,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(568,5,25,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(569,3,6,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(570,4,6,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(571,5,6,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(572,3,22,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(573,4,22,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(574,5,22,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(575,3,13,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(576,4,13,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(577,5,13,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(578,3,33,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(579,4,33,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(580,5,33,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(581,3,17,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(582,4,17,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(583,5,17,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(584,3,37,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(585,4,37,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(586,5,37,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(587,3,3,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(588,4,3,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(589,5,3,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(590,3,24,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(591,4,24,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(592,5,24,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(593,3,4,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(594,4,4,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(595,5,4,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(596,3,12,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(597,4,12,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(598,5,12,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(599,3,32,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(600,4,32,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(601,5,32,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(602,3,11,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(603,4,11,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(604,5,11,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(605,3,31,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(606,4,31,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(607,5,31,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(608,3,18,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(609,4,18,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(610,5,18,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(611,3,38,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(612,4,38,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(613,5,38,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(614,3,39,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(615,4,39,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(616,5,39,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(617,3,19,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(618,4,19,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(619,5,19,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(620,3,29,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(621,4,29,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(622,5,29,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(623,3,9,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(624,4,9,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(625,5,9,0,'2025-11-26 11:42:43','2025-11-26 11:42:43'),
(626,3,41,100,'2025-11-26 11:42:57','2025-11-26 11:42:57'),
(627,4,41,100,'2025-11-26 11:42:57','2025-11-26 11:42:57'),
(628,5,41,100,'2025-11-26 11:42:57','2025-11-26 11:42:57');
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
) ENGINE=InnoDB AUTO_INCREMENT=42 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students`
--

LOCK TABLES `students` WRITE;
/*!40000 ALTER TABLE `students` DISABLE KEYS */;
INSERT INTO `students` VALUES
(1,4,3,'BSIT','Programming',2,'1A',NULL,NULL,NULL,'2025-11-18 20:54:05'),
(2,5,4,'BSIT','Programming',2,'1A',NULL,NULL,NULL,'2025-11-18 20:54:05'),
(3,6,5,'BSIT','Programming',2,'1A',NULL,NULL,NULL,'2025-11-18 20:54:05'),
(4,7,6,'BSIT','Programming',2,'1A',NULL,NULL,NULL,'2025-11-18 20:54:05'),
(5,8,7,'BSIT','Programming',2,'1A',NULL,NULL,NULL,'2025-11-18 20:54:05'),
(6,9,8,'BSIT','Programming',2,'1A',NULL,NULL,NULL,'2025-11-18 20:54:05'),
(7,10,9,'BSIT','Programming',2,'1A',NULL,NULL,NULL,'2025-11-18 20:54:05'),
(8,11,10,'BSIT','Programming',2,'1A',NULL,NULL,NULL,'2025-11-18 20:54:05'),
(9,12,11,'BSIT','Programming',2,'1A',NULL,NULL,NULL,'2025-11-18 20:54:05'),
(10,13,12,'BSIT','Programming',2,'1A',NULL,NULL,NULL,'2025-11-18 20:54:05'),
(11,14,13,'BSIT','Programming',2,'1A',NULL,NULL,NULL,'2025-11-18 20:54:05'),
(12,15,14,'BSIT','Programming',2,'1A',NULL,NULL,NULL,'2025-11-18 20:54:05'),
(13,16,15,'BSIT','Programming',2,'1A',NULL,NULL,NULL,'2025-11-18 20:54:05'),
(14,17,16,'BSIT','Programming',2,'1A',NULL,NULL,NULL,'2025-11-18 20:54:05'),
(15,18,17,'BSIT','Programming',2,'1A',NULL,NULL,NULL,'2025-11-18 20:54:05'),
(16,19,18,'BSIT','Programming',2,'1A',NULL,NULL,NULL,'2025-11-18 20:54:05'),
(17,20,19,'BSIT','Programming',2,'1A',NULL,NULL,NULL,'2025-11-18 20:54:05'),
(18,21,20,'BSIT','Programming',2,'1A',NULL,NULL,NULL,'2025-11-18 20:54:05'),
(19,22,21,'BSIT','Programming',2,'1A',NULL,NULL,NULL,'2025-11-18 20:54:05'),
(20,23,22,'BSIT','Programming',2,'1A',NULL,NULL,NULL,'2025-11-18 20:54:05'),
(21,24,23,'BSIT','Programming',2,'1A',NULL,NULL,NULL,'2025-11-18 20:58:53'),
(22,25,24,'BSIT','Programming',2,'1A',NULL,NULL,NULL,'2025-11-18 20:58:53'),
(23,26,25,'BSIT','Programming',2,'1A',NULL,NULL,NULL,'2025-11-18 20:58:53'),
(24,27,26,'BSIT','Programming',2,'1A',NULL,NULL,NULL,'2025-11-18 20:58:53'),
(25,28,27,'BSIT','Programming',2,'1A',NULL,NULL,NULL,'2025-11-18 20:58:53'),
(26,29,28,'BSIT','Programming',2,'1A',NULL,NULL,NULL,'2025-11-18 20:58:53'),
(27,30,29,'BSIT','Programming',2,'1A',NULL,NULL,NULL,'2025-11-18 20:58:53'),
(28,31,30,'BSIT','Programming',2,'1A',NULL,NULL,NULL,'2025-11-18 20:58:53'),
(29,32,31,'BSIT','Programming',2,'1A',NULL,NULL,NULL,'2025-11-18 20:58:53'),
(30,33,32,'BSIT','Programming',2,'1A',NULL,NULL,NULL,'2025-11-18 20:58:53'),
(31,34,33,'BSIT','Programming',2,'1A',NULL,NULL,NULL,'2025-11-18 20:58:53'),
(32,35,34,'BSIT','Programming',2,'1A',NULL,NULL,NULL,'2025-11-18 20:58:53'),
(33,36,35,'BSIT','Programming',2,'1A',NULL,NULL,NULL,'2025-11-18 20:58:53'),
(34,37,36,'BSIT','Programming',2,'1A',NULL,NULL,NULL,'2025-11-18 20:58:53'),
(35,38,37,'BSIT','Programming',2,'1A',NULL,NULL,NULL,'2025-11-18 20:58:53'),
(36,39,38,'BSIT','Programming',2,'1A',NULL,NULL,NULL,'2025-11-18 20:58:53'),
(37,40,39,'BSIT','Programming',2,'1A',NULL,NULL,NULL,'2025-11-18 20:58:53'),
(38,41,40,'BSIT','Programming',2,'1A',NULL,NULL,NULL,'2025-11-18 20:58:53'),
(39,42,41,'BSIT','Programming',2,'1A',NULL,NULL,NULL,'2025-11-18 20:58:53'),
(40,43,42,'BSIT','Programming',2,'1A',NULL,NULL,NULL,'2025-11-18 20:58:53'),
(41,44,43,'BSIT','Networking',2,'A',NULL,NULL,NULL,'2025-11-19 19:06:03');
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
) ENGINE=InnoDB AUTO_INCREMENT=45 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES
(1,'admin001','scrypt:32768:8:1$WOv7GyeczVCC9BB7$d30e4347fca06f7e94b4bd6eaa4658abb2cb0b1cad540d182e47e7860d0043594d5a57cde3e7a72272e27e92293c0496abe8db13c3c98183bbd1ed8a95001f60','admin','2025-11-16 18:14:47'),
(2,'INS-007','scrypt:32768:8:1$oXcyRnRUy2Dnajmf$82e49aa5f24193394efc90e047f1a8b1c003681e7c2fc4e3b1af046c655305fbc7c36087edb6b2ddad6651f158bb6cba14f0e2e3cb7392f50f5920a75c046c82','instructor','2025-11-16 18:34:41'),
(3,'INS-009','scrypt:32768:8:1$7Wojs8o5W9phXcII$195509aa7eee0752e0f5dd372c2f1ba4bc16ef03dd01e03df51645e00c1bee1c0592b8c59f2f242dd944f342b9eb37e993f60515e7694b9a48fac6a3f50ea28f','instructor','2025-11-16 18:37:27'),
(4,'20240001','scrypt:32768:8:1$dummy$dummyhash123','student','2025-11-18 20:54:05'),
(5,'20240002','scrypt:32768:8:1$dummy$dummyhash123','student','2025-11-18 20:54:05'),
(6,'20240003','scrypt:32768:8:1$dummy$dummyhash123','student','2025-11-18 20:54:05'),
(7,'20240004','scrypt:32768:8:1$dummy$dummyhash123','student','2025-11-18 20:54:05'),
(8,'20240005','scrypt:32768:8:1$dummy$dummyhash123','student','2025-11-18 20:54:05'),
(9,'20240006','scrypt:32768:8:1$dummy$dummyhash123','student','2025-11-18 20:54:05'),
(10,'20240007','scrypt:32768:8:1$dummy$dummyhash123','student','2025-11-18 20:54:05'),
(11,'20240008','scrypt:dummy$dummyhash123','student','2025-11-18 20:54:05'),
(12,'20240009','scrypt:32768:8:1$dummy$dummyhash123','student','2025-11-18 20:54:05'),
(13,'20240010','scrypt:32768:8:1$dummy$dummyhash123','student','2025-11-18 20:54:05'),
(14,'20240011','scrypt:32768:8:1$dummy$dummyhash123','student','2025-11-18 20:54:05'),
(15,'20240012','scrypt:32768:8:1$dummy$dummyhash123','student','2025-11-18 20:54:05'),
(16,'20240013','scrypt:32768:8:1$dummy$dummyhash123','student','2025-11-18 20:54:05'),
(17,'20240014','scrypt:32768:8:1$dummy$dummyhash123','student','2025-11-18 20:54:05'),
(18,'20240015','scrypt:32768:8:1$dummy$dummyhash123','student','2025-11-18 20:54:05'),
(19,'20240016','scrypt:32768:8:1$dummy$dummyhash123','student','2025-11-18 20:54:05'),
(20,'20240017','scrypt:32768:8:1$dummy$dummyhash123','student','2025-11-18 20:54:05'),
(21,'20240018','scrypt:32768:8:1$dummy$dummyhash123','student','2025-11-18 20:54:05'),
(22,'20240019','scrypt:32768:8:1$dummy$dummyhash123','student','2025-11-18 20:54:05'),
(23,'20240020','scrypt:32768:8:1$dummy$dummyhash123','student','2025-11-18 20:54:05'),
(24,'20240021','scrypt:32768:8:1$dummy$dummyhash123','student','2025-11-18 20:58:53'),
(25,'20240022','scrypt:32768:8:1$dummy$dummyhash123','student','2025-11-18 20:58:53'),
(26,'20240023','scrypt:32768:8:1$dummy$dummyhash123','student','2025-11-18 20:58:53'),
(27,'20240024','scrypt:32768:8:1$dummy$dummyhash123','student','2025-11-18 20:58:53'),
(28,'20240025','scrypt:32768:8:1$dummy$dummyhash123','student','2025-11-18 20:58:53'),
(29,'20240026','scrypt:32768:8:1$dummy$dummyhash123','student','2025-11-18 20:58:53'),
(30,'20240027','scrypt:32768:8:1$dummy$dummyhash123','student','2025-11-18 20:58:53'),
(31,'20240028','scrypt:32768:8:1$dummy$dummyhash123','student','2025-11-18 20:58:53'),
(32,'20240029','scrypt:32768:8:1$dummy$dummyhash123','student','2025-11-18 20:58:53'),
(33,'20240030','scrypt:32768:8:1$dummy$dummyhash123','student','2025-11-18 20:58:53'),
(34,'20240031','scrypt:32768:8:1$dummy$dummyhash123','student','2025-11-18 20:58:53'),
(35,'20240032','scrypt:32768:8:1$dummy$dummyhash123','student','2025-11-18 20:58:53'),
(36,'20240033','scrypt:32768:8:1$dummy$dummyhash123','student','2025-11-18 20:58:53'),
(37,'20240034','scrypt:32768:8:1$dummy$dummyhash123','student','2025-11-18 20:58:53'),
(38,'20240035','scrypt:32768:8:1$dummy$dummyhash123','student','2025-11-18 20:58:53'),
(39,'20240036','scrypt:32768:8:1$dummy$dummyhash123','student','2025-11-18 20:58:53'),
(40,'20240037','scrypt:32768:8:1$dummy$dummyhash123','student','2025-11-18 20:58:53'),
(41,'20240038','scrypt:32768:8:1$dummy$dummyhash123','student','2025-11-18 20:58:53'),
(42,'20240039','scrypt:32768:8:1$dummy$dummyhash123','student','2025-11-18 20:58:53'),
(43,'20240040','scrypt:32768:8:1$dummy$dummyhash123','student','2025-11-18 20:58:53'),
(44,'23-13439','scrypt:32768:8:1$NQUpGLCUNgGcfZJK$241e25370865e868f149bcedab1ff15ac8bde62d23b6a5bc02ae93fd7176eef6c11c66dd9a382e2c50a0de4f07d62787256e9345697cf9b20d380318051ad913','student','2025-11-19 19:06:03');
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

-- Dump completed on 2025-11-26 20:00:49
