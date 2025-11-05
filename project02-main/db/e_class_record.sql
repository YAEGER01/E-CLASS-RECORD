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
  `class_type` varchar(10) DEFAULT NULL,
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
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `classes`
--

LOCK TABLES `classes` WRITE;
/*!40000 ALTER TABLE `classes` DISABLE KEYS */;
INSERT INTO `classes` VALUES
(1,1,'MINOR','2024','1st sem','BSIT','Programming','1A','M-W-F 8-10AM','e1726fb2-2b7b-4084-94d2-3f1cd08880f9','331922',NULL,'2025-10-26 14:30:40','2025-10-26 14:30:40'),
(2,1,'MAJOR','2024','2nd sem','BSIT','Networking','2B','M-W-F 8-10AM','13db6c7b-30c5-43cc-89b9-b5452f23206c','536608',NULL,'2025-10-26 14:31:05','2025-10-26 14:31:05'),
(3,1,'MAJOR','2024','1st sem','BSIT','Networking','3A','M-W-F 8-10AM','4aadc054-4d66-46a0-8159-d53fe5fe6d94','879220',NULL,'2025-10-31 12:37:02','2025-10-31 12:37:02'),
(4,1,'MAJOR','2069','1st sem','BSIT','Database','3C','T-Th 10-12PM','c8c4747f-0541-4f40-8b45-ed559d16c9e7','764509',NULL,'2025-11-01 20:04:50','2025-11-01 20:04:50');
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
) ENGINE=InnoDB AUTO_INCREMENT=24 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `grade_assessments`
--

LOCK TABLES `grade_assessments` WRITE;
/*!40000 ALTER TABLE `grade_assessments` DISABLE KEYS */;
INSERT INTO `grade_assessments` VALUES
(1,16,'Attendance',NULL,100,NULL,1,NULL,'2025-11-01 21:15:28'),
(2,17,'Attitude',NULL,100,NULL,1,NULL,'2025-11-01 21:15:43'),
(3,18,'Participation',NULL,100,NULL,1,NULL,'2025-11-01 21:15:55'),
(4,19,'Homework',NULL,100,NULL,1,NULL,'2025-11-01 21:16:03'),
(5,20,'Excercise 1',NULL,50,NULL,1,NULL,'2025-11-01 21:16:21'),
(6,20,'Excercise 2',NULL,100,NULL,2,NULL,'2025-11-01 21:16:30'),
(7,16,'Attendance 2',NULL,100,NULL,2,NULL,'2025-11-01 21:27:40'),
(8,16,'Assessment 1',NULL,100,NULL,3,NULL,'2025-11-01 21:32:03'),
(9,18,'Participation 2',NULL,100,NULL,2,NULL,'2025-11-01 21:36:37'),
(10,18,'Participation 3',NULL,100,NULL,3,NULL,'2025-11-01 21:36:42'),
(11,18,'Participation 4',NULL,100,NULL,4,NULL,'2025-11-01 21:36:46'),
(12,18,'Participation 5',NULL,100,NULL,5,NULL,'2025-11-01 21:36:51'),
(13,18,'Participation 6',NULL,100,NULL,6,NULL,'2025-11-01 21:36:53'),
(14,18,'Participation 7',NULL,100,NULL,7,NULL,'2025-11-01 21:36:56'),
(15,18,'Participation 8',NULL,100,NULL,8,NULL,'2025-11-01 21:36:58'),
(16,18,'Participation 9',NULL,100,NULL,9,NULL,'2025-11-01 21:37:00'),
(17,18,'Participation 10',NULL,100,NULL,10,NULL,'2025-11-01 21:37:03'),
(18,20,'Excercise 3',NULL,100,NULL,3,NULL,'2025-11-01 21:37:08'),
(19,18,'Participation 11',NULL,100,NULL,11,NULL,'2025-11-01 21:37:10'),
(20,18,'Participation 12',NULL,100,NULL,12,NULL,'2025-11-01 21:37:12'),
(21,17,'Attitude',NULL,100,NULL,2,NULL,'2025-11-01 21:37:22'),
(22,19,'Homework',NULL,100,NULL,2,NULL,'2025-11-01 21:37:28'),
(23,20,'Excercise 4',NULL,100,NULL,4,NULL,'2025-11-01 21:37:33');
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
  CONSTRAINT `fk_structure` FOREIGN KEY (`structure_id`) REFERENCES `grade_structures` (`id`) ON DELETE CASCADE,
  CONSTRAINT `grade_categories_ibfk_1` FOREIGN KEY (`structure_id`) REFERENCES `grade_structures` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `grade_categories`
--

LOCK TABLES `grade_categories` WRITE;
/*!40000 ALTER TABLE `grade_categories` DISABLE KEYS */;
INSERT INTO `grade_categories` VALUES
(3,7,'LECTURE',100,1,NULL,'2025-11-01 20:57:55'),
(4,7,'LABORATORY',100,2,NULL,'2025-11-01 20:57:55');
/*!40000 ALTER TABLE `grade_categories` ENABLE KEYS */;
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
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
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
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `grade_structures`
--

LOCK TABLES `grade_structures` WRITE;
/*!40000 ALTER TABLE `grade_structures` DISABLE KEYS */;
INSERT INTO `grade_structures` VALUES
(7,1,'BSIT 1a','{\"LABORATORY\": [{\"name\": \"LAB PARTICIPATION\", \"weight\": 25, \"assessments\": []}, {\"name\": \"LAB HOMEWORK\", \"weight\": 50, \"assessments\": []}, {\"name\": \"LAB EXERCISE\", \"weight\": 25, \"assessments\": []}], \"LECTURE\": [{\"name\": \"ATTENDANCE\", \"weight\": 50, \"assessments\": []}, {\"name\": \"ATTITUDE\", \"weight\": 50, \"assessments\": []}]}',1,'2025-11-01 13:11:39','2025-11-01 20:40:14',1,1),
(11,4,'TEST','{\"LABORATORY\": [{\"name\": \"LAB PARTICIPATION\", \"weight\": 5, \"assessments\": []}, {\"name\": \"LAB HOMEWORK\", \"weight\": 10, \"assessments\": []}, {\"name\": \"LAB EXERCISE\", \"weight\": 15, \"assessments\": []}, {\"name\": \"PRELIM LAB EXAM\", \"weight\": 20, \"assessments\": []}, {\"name\": \"MIDTERM LAB EXAM\", \"weight\": 25, \"assessments\": []}, {\"name\": \"FINAL LAB EXAM\", \"weight\": 25, \"assessments\": []}], \"LECTURE\": [{\"name\": \"ATTENDANCE\", \"weight\": 25, \"assessments\": []}, {\"name\": \"ATTITUDE\", \"weight\": 25, \"assessments\": []}, {\"name\": \"ATTITUDE\", \"weight\": 50, \"assessments\": []}]}',1,'2025-11-01 20:42:02','2025-11-01 20:42:02',1,1);
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
) ENGINE=InnoDB AUTO_INCREMENT=21 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `grade_subcategories`
--

LOCK TABLES `grade_subcategories` WRITE;
/*!40000 ALTER TABLE `grade_subcategories` DISABLE KEYS */;
INSERT INTO `grade_subcategories` VALUES
(16,3,'ATTENDANCE',50,0,NULL,1,NULL,'2025-11-01 20:57:55'),
(17,3,'ATTITUDE',50,0,NULL,2,NULL,'2025-11-01 20:57:55'),
(18,4,'LAB PARTICIPATION',25,0,NULL,1,NULL,'2025-11-01 20:57:55'),
(19,4,'LAB HOMEWORK',50,0,NULL,2,NULL,'2025-11-01 20:57:55'),
(20,4,'LAB EXERCISE',25,0,NULL,3,NULL,'2025-11-01 20:57:55');
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
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `instructors`
--

LOCK TABLES `instructors` WRITE;
/*!40000 ALTER TABLE `instructors` DISABLE KEYS */;
INSERT INTO `instructors` VALUES
(1,2,1,'Information Technology','NS','CL-001',NULL,'active','2025-10-26 14:29:59','2025-11-03 11:45:04');
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
) ENGINE=InnoDB AUTO_INCREMENT=24 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `personal_info`
--

LOCK TABLES `personal_info` WRITE;
/*!40000 ALTER TABLE `personal_info` DISABLE KEYS */;
INSERT INTO `personal_info` VALUES
(1,'Frederick','Madayag',NULL,'frederick.madayag_cyn@isu.edu.ph','09277102690','CYN CITY','1986-05-04','Male','Frederick Madayag','09277102690','2025-10-26 14:29:59','2025-10-26 14:29:59'),
(2,'Juan','Garcia','Santos','juan.garcia@isu.edu.ph','09271234567','Cauayan City','2003-05-15','Male','Maria Garcia','09289876543','2025-10-30 23:58:33','2025-10-30 23:58:33'),
(3,'Maria','Santos','Cruz','maria.santos@isu.edu.ph','09261234568','Santiago City','2003-08-22','Female','Pedro Santos','09291234567','2025-10-30 23:58:33','2025-10-30 23:58:33'),
(4,'Miguel','Reyes','Luna','miguel.reyes@isu.edu.ph','09273456789','Cauayan City','2004-03-10','Male','Ana Reyes','09282345678','2025-10-30 23:58:33','2025-10-30 23:58:33'),
(5,'Sofia','Cruz','Rivera','sofia.cruz@isu.edu.ph','09254567890','Santiago City','2003-11-28','Female','Manuel Cruz','09287654321','2025-10-30 23:58:33','2025-10-30 23:58:33'),
(6,'Gabriel','Luna','Torres','gabriel.luna@isu.edu.ph','09265678901','Cauayan City','2004-01-15','Male','Isabel Luna','09283456789','2025-10-30 23:58:33','2025-10-30 23:58:33'),
(7,'Isabella','Torres','Garcia','isabella.torres@isu.edu.ph','09276789012','Santiago City','2003-07-20','Female','Ricardo Torres','09284567890','2025-10-30 23:58:33','2025-10-30 23:58:33'),
(8,'Lucas','Rivera','Santos','lucas.rivera@isu.edu.ph','09287890123','Cauayan City','2004-05-03','Male','Carmen Rivera','09285678901','2025-10-30 23:58:33','2025-10-30 23:58:33'),
(9,'Emma','Martinez','Cruz','emma.martinez@isu.edu.ph','09268901234','Santiago City','2003-09-12','Female','Luis Martinez','09286789012','2025-10-30 23:58:33','2025-10-30 23:58:33'),
(10,'Daniel','Flores','Reyes','daniel.flores@isu.edu.ph','09259012345','Cauayan City','2004-02-28','Male','Rosa Flores','09287890123','2025-10-30 23:58:33','2025-10-30 23:58:33'),
(11,'Victoria','Ramos','Luna','victoria.ramos@isu.edu.ph','09270123456','Santiago City','2003-12-05','Female','Juan Ramos','09288901234','2025-10-30 23:58:33','2025-10-30 23:58:33'),
(22,'Student','User',NULL,'2025-TEST-0001@student.edu',NULL,NULL,NULL,NULL,NULL,NULL,'2025-11-01 23:16:53','2025-11-01 23:16:53'),
(23,'Student','User',NULL,'23-13333@student.edu',NULL,NULL,NULL,NULL,NULL,NULL,'2025-11-01 23:22:24','2025-11-01 23:22:24');
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
) ENGINE=InnoDB AUTO_INCREMENT=21 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `student_classes`
--

LOCK TABLES `student_classes` WRITE;
/*!40000 ALTER TABLE `student_classes` DISABLE KEYS */;
INSERT INTO `student_classes` VALUES
(1,1,1,'2025-10-30 23:58:33'),
(2,2,1,'2025-10-30 23:58:33'),
(3,3,2,'2025-10-30 23:58:33'),
(4,4,1,'2025-10-30 23:58:33'),
(5,5,2,'2025-10-30 23:58:33'),
(6,6,1,'2025-10-30 23:58:33'),
(7,7,2,'2025-10-30 23:58:33'),
(8,8,1,'2025-10-30 23:58:33'),
(9,9,2,'2025-10-30 23:58:33'),
(10,10,1,'2025-10-30 23:58:38'),
(11,11,1,'2025-10-30 23:58:43'),
(12,12,1,'2025-10-30 23:58:43'),
(13,13,2,'2025-10-30 23:58:43'),
(14,13,1,'2025-10-30 23:58:43');
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
) ENGINE=InnoDB AUTO_INCREMENT=23 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students`
--

LOCK TABLES `students` WRITE;
/*!40000 ALTER TABLE `students` DISABLE KEYS */;
INSERT INTO `students` VALUES
(1,3,2,'BSIT','Programming',2,'1A',NULL,NULL,NULL,'2025-10-30 23:58:33'),
(2,4,3,'BSIT','Programming',2,'1A',NULL,NULL,NULL,'2025-10-30 23:58:33'),
(3,5,4,'BSIT','Networking',2,'2B',NULL,NULL,NULL,'2025-10-30 23:58:33'),
(4,6,5,'BSIT','Programming',2,'1A',NULL,NULL,NULL,'2025-10-30 23:58:33'),
(5,7,6,'BSIT','Networking',2,'2B',NULL,NULL,NULL,'2025-10-30 23:58:33'),
(6,8,7,'BSIT','Programming',2,'1A',NULL,NULL,NULL,'2025-10-30 23:58:33'),
(7,9,8,'BSIT','Networking',2,'2B',NULL,NULL,NULL,'2025-10-30 23:58:33'),
(8,10,9,'BSIT','Programming',2,'1A',NULL,NULL,NULL,'2025-10-30 23:58:33'),
(9,11,10,'BSIT','Networking',2,'2B',NULL,NULL,NULL,'2025-10-30 23:58:33'),
(10,12,11,'BSIT','Programming',2,'1A',NULL,NULL,NULL,'2025-10-30 23:58:33'),
(11,10,2,'BSIT','Programming',2,'1A',NULL,NULL,NULL,'2025-10-30 23:58:43'),
(12,11,3,'BSIT','Programming',2,'1A',NULL,NULL,NULL,'2025-10-30 23:58:43'),
(13,12,4,'BSIT','Networking',2,'2B',NULL,NULL,NULL,'2025-10-30 23:58:43'),
(21,23,22,'BSIT',NULL,1,'A',NULL,NULL,NULL,'2025-11-01 23:16:53'),
(22,24,23,'BSIT','Networking',3,'A',NULL,NULL,NULL,'2025-11-01 23:22:24');
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
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES
(1,'admin001','scrypt:32768:8:1$w7mnsr1qlaUQtS05$c0f059d7b2827d3110f0fbdfbb725824687c68f0990dfb6d989a2430f11920e2d033c68b78bd44e99f12491e35fceb6ea0313769213ebb7323715176ecab2c59','admin','2025-10-25 21:20:33'),
(2,'CL-001','scrypt:32768:8:1$yegeDg0HVdUPbNK1$738898057481bed649a73067c5f0505319e449477409d07679e8945ac04062a8780b3429dc860ded844461d55717d473bc6cc15cba71ba4a4fb76d5a3d671786','instructor','2025-10-26 14:29:59'),
(3,'2023-00001','scrypt:32768:8:1$default_hash$student_password_hash','student','2025-10-30 23:58:33'),
(4,'2023-00002','scrypt:32768:8:1$default_hash$student_password_hash','student','2025-10-30 23:58:33'),
(5,'2023-00003','scrypt:32768:8:1$default_hash$student_password_hash','student','2025-10-30 23:58:33'),
(6,'2023-00004','scrypt:32768:8:1$default_hash$student_password_hash','student','2025-10-30 23:58:33'),
(7,'2023-00005','scrypt:32768:8:1$default_hash$student_password_hash','student','2025-10-30 23:58:33'),
(8,'2023-00006','scrypt:32768:8:1$default_hash$student_password_hash','student','2025-10-30 23:58:33'),
(9,'2023-00007','scrypt:32768:8:1$default_hash$student_password_hash','student','2025-10-30 23:58:33'),
(10,'2023-00008','scrypt:32768:8:1$default_hash$student_password_hash','student','2025-10-30 23:58:33'),
(11,'2023-00009','scrypt:32768:8:1$default_hash$student_password_hash','student','2025-10-30 23:58:33'),
(12,'2023-00010','scrypt:32768:8:1$default_hash$student_password_hash','student','2025-10-30 23:58:33'),
(23,'2025-TEST-0001','scrypt:32768:8:1$DVHtC2bNZ22oFzrT$7f3619eb0cdf82845a894c20a7184860641ee24cc83a09287203acec0842dc2b89ff5eec68686cbdcaa63ca8298fff3e7e90a542b335f01f94d1ed9ae28c264c','student','2025-11-01 23:16:53'),
(24,'23-13333','scrypt:32768:8:1$PqGSGWpYElVqligb$d1399c7c39a48dc2f0fe2c61b7258b8dd42cfbd5a6b6ae04ff1956b4b722cbe97a2113679c47b44ecfa7216d89a9b9fae38151c63766b9f9e5bda45826f0b609','student','2025-11-01 23:22:24');
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

-- Dump completed on 2025-11-03 13:37:22
