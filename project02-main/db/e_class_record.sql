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
(1,1,'MAJOR','2024','1st sem','BSIT','Ako BUdoy 101','Networking','1A','M-W-F 8-10AM','19a3532f-1ec9-4cbe-9595-672eadc6a8ba','946205',NULL,'2025-11-07 09:57:46','2025-11-14 14:28:15');
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
) ENGINE=InnoDB AUTO_INCREMENT=30 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `grade_assessments`
--

LOCK TABLES `grade_assessments` WRITE;
/*!40000 ALTER TABLE `grade_assessments` DISABLE KEYS */;
INSERT INTO `grade_assessments` VALUES
(6,20,'Lab Participation',NULL,15,NULL,1,NULL,'2025-11-13 19:51:17'),
(7,20,'Lab Participation 2',NULL,25,NULL,2,NULL,'2025-11-13 19:51:34'),
(8,21,'Lab Homework',NULL,10,NULL,1,NULL,'2025-11-13 20:02:02'),
(9,21,'Lab Homework 2',NULL,25,NULL,2,NULL,'2025-11-13 20:02:18'),
(10,22,'Assessment 1',NULL,25,NULL,1,NULL,'2025-11-14 11:28:13'),
(11,22,'Assessment 2',NULL,30,NULL,2,NULL,'2025-11-14 11:31:08'),
(12,23,'Assessment 1',NULL,50,NULL,1,NULL,'2025-11-14 11:31:24'),
(13,24,'Assessment 1',NULL,70,NULL,1,NULL,'2025-11-14 11:31:33'),
(14,25,'Assessment 1',NULL,80,NULL,1,NULL,'2025-11-14 11:31:43'),
(15,11,'Assessment 1',NULL,15,NULL,1,NULL,'2025-11-14 11:37:32'),
(16,11,'Assessment 2',NULL,15,NULL,2,NULL,'2025-11-14 11:37:40'),
(17,12,'Assessment 1',NULL,10,NULL,1,NULL,'2025-11-14 11:37:50'),
(18,12,'Assessment 2',NULL,10,NULL,2,NULL,'2025-11-14 11:38:03'),
(20,13,'Reci',NULL,15,NULL,1,NULL,'2025-11-14 11:38:40'),
(21,13,'Reci 1',NULL,15,NULL,2,NULL,'2025-11-14 11:38:51'),
(22,14,'Assessment 1',NULL,20,NULL,1,NULL,'2025-11-14 11:39:00'),
(23,14,'Assessment 2',NULL,20,NULL,2,NULL,'2025-11-14 11:39:20'),
(24,15,'Assessment 1',NULL,15,NULL,1,NULL,'2025-11-14 11:39:38'),
(25,15,'Assessment 2',NULL,20,NULL,2,NULL,'2025-11-14 11:39:49'),
(26,16,'Assessment 3',NULL,50,NULL,1,NULL,'2025-11-14 11:40:14'),
(27,17,'Exam',NULL,60,NULL,1,NULL,'2025-11-14 11:40:30'),
(28,18,'Exam',NULL,60,NULL,1,NULL,'2025-11-14 11:41:18'),
(29,19,'Exam',NULL,70,NULL,1,NULL,'2025-11-14 11:42:50');
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
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `grade_categories`
--

LOCK TABLES `grade_categories` WRITE;
/*!40000 ALTER TABLE `grade_categories` DISABLE KEYS */;
INSERT INTO `grade_categories` VALUES
(4,11,'LECTURE',100,1,NULL,'2025-11-13 19:48:29'),
(5,11,'LABORATORY',100,2,NULL,'2025-11-13 19:48:29');
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
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `grade_structures`
--

LOCK TABLES `grade_structures` WRITE;
/*!40000 ALTER TABLE `grade_structures` DISABLE KEYS */;
INSERT INTO `grade_structures` VALUES
(11,1,'TEST 1','{\"LABORATORY\": [{\"name\": \"LAB PARTICIPATION\", \"weight\": 5, \"assessments\": []}, {\"name\": \"LAB HOMEWORK\", \"weight\": 10, \"assessments\": []}, {\"name\": \"LAB EXERCISE\", \"weight\": 15, \"assessments\": []}, {\"name\": \"PRELIM LAB EXAM\", \"weight\": 20, \"assessments\": []}, {\"name\": \"MIDTERM LAB EXAM\", \"weight\": 25, \"assessments\": []}, {\"name\": \"FINAL LAB EXAM\", \"weight\": 25, \"assessments\": []}], \"LECTURE\": [{\"name\": \"ATTENDANCE\", \"weight\": 2.5, \"assessments\": []}, {\"name\": \"ATTITUDE\", \"weight\": 2.5, \"assessments\": []}, {\"name\": \"RECITATION\", \"weight\": 2.5, \"assessments\": []}, {\"name\": \"HOMEWORK\", \"weight\": 2.5, \"assessments\": []}, {\"name\": \"QUIZ\", \"weight\": 15, \"assessments\": []}, {\"name\": \"PROJECT\", \"weight\": 10, \"assessments\": []}, {\"name\": \"PRELIM EXAM\", \"weight\": 15, \"assessments\": []}, {\"name\": \"MIDTERM EXAM\", \"weight\": 25, \"assessments\": []}, {\"name\": \"FINAL EXAM\", \"weight\": 25, \"assessments\": []}]}',1,'2025-11-13 19:48:19','2025-11-13 22:59:46',1,1);
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
) ENGINE=InnoDB AUTO_INCREMENT=26 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `grade_subcategories`
--

LOCK TABLES `grade_subcategories` WRITE;
/*!40000 ALTER TABLE `grade_subcategories` DISABLE KEYS */;
INSERT INTO `grade_subcategories` VALUES
(11,4,'ATTENDANCE',2.5,0,NULL,1,NULL,'2025-11-13 19:48:29'),
(12,4,'ATTITUDE',2.5,0,NULL,2,NULL,'2025-11-13 19:48:29'),
(13,4,'RECITATION',2.5,0,NULL,3,NULL,'2025-11-13 19:48:29'),
(14,4,'HOMEWORK',2.5,0,NULL,4,NULL,'2025-11-13 19:48:29'),
(15,4,'QUIZ',15,0,NULL,5,NULL,'2025-11-13 19:48:29'),
(16,4,'PROJECT',10,0,NULL,6,NULL,'2025-11-13 19:48:29'),
(17,4,'PRELIM EXAM',15,0,NULL,7,NULL,'2025-11-13 19:48:29'),
(18,4,'MIDTERM EXAM',25,0,NULL,8,NULL,'2025-11-13 19:48:29'),
(19,4,'FINAL EXAM',25,0,NULL,9,NULL,'2025-11-13 19:48:29'),
(20,5,'LAB PARTICIPATION',5,0,NULL,1,NULL,'2025-11-13 19:48:29'),
(21,5,'LAB HOMEWORK',10,0,NULL,2,NULL,'2025-11-13 19:48:29'),
(22,5,'LAB EXERCISE',15,0,NULL,3,NULL,'2025-11-13 19:48:29'),
(23,5,'PRELIM LAB EXAM',20,0,NULL,4,NULL,'2025-11-13 19:48:29'),
(24,5,'MIDTERM LAB EXAM',25,0,NULL,5,NULL,'2025-11-13 19:48:29'),
(25,5,'FINAL LAB EXAM',25,0,NULL,6,NULL,'2025-11-13 19:48:29');
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
(1,2,1,'Information Technology','MWEHEHE','CL_001',NULL,'active','2025-11-07 09:56:56','2025-11-07 09:56:56');
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
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `personal_info`
--

LOCK TABLES `personal_info` WRITE;
/*!40000 ALTER TABLE `personal_info` DISABLE KEYS */;
INSERT INTO `personal_info` VALUES
(1,'Frederick','Madayag',NULL,'frederick.madayag_cyn@isu.edu.ph','09277102690','asukdguakdgaskj','1999-11-02','Male','iosdfh','09277102690','2025-11-07 09:56:56','2025-11-07 09:56:56'),
(2,'AKOooooooo','FREDDDDDDDDDDDD','','23-13439@student.edu','','BAHAHAHHAHAHAY',NULL,'Male','','','2025-11-07 09:58:59','2025-11-07 11:16:37');
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
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `student_classes`
--

LOCK TABLES `student_classes` WRITE;
/*!40000 ALTER TABLE `student_classes` DISABLE KEYS */;
INSERT INTO `student_classes` VALUES
(1,1,1,'2025-11-07 10:02:26');
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
  CONSTRAINT `student_scores_ibfk_1` FOREIGN KEY (`assessment_id`) REFERENCES `assessments` (`id`) ON DELETE CASCADE,
  CONSTRAINT `student_scores_ibfk_2` FOREIGN KEY (`student_id`) REFERENCES `students` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
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
(1,3,2,'BSIT','Networking',1,'A','uploads/88f647da23eb4facad9fa11f2b082b4f_IMG_20251103_171505.jpg','uploads/2c4d6d647058421186a0a3e44d89285f_IMG_20251103_171505.jpg','uploads/ffa99f3a5b2948d8924e94646f1ac73e_IMG_20251103_171505.jpg','2025-11-07 09:58:59');
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
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES
(1,'admin001','scrypt:32768:8:1$G4jyO3RAfHGPaVjg$36f40df2e16de8a695dc891da2a8841fc0e4fe8dd7efd9797a3317951de469108eb381b5d44be14fbb7a3e8c0c264f0a647ef4bc0b18749cf3c40ec565ff7d27','admin','2025-11-07 09:46:01'),
(2,'CL_001','scrypt:32768:8:1$iqJHjBDcDeVYjowW$d8d0cf849ef83387ed192485506ca3f77e0a07d8d7fb664a4d30b5a6c3c472d5e27953b502ee6021a75176267c9bbfc72399af51bb67fe36b73ec6c0f4c1ee16','instructor','2025-11-07 09:56:56'),
(3,'23-13439','scrypt:32768:8:1$kksumUyiHg5tEC2O$ae430078c5b0cbb3c05c8d348d470badcc83929ad5fc66704e9406a4667948cd2722aa9a01b33bfd549d479211aab7ee63a3f3ce3782ad1f34af289fe4ada5e7','student','2025-11-07 09:58:59');
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

-- Dump completed on 2025-11-14 15:24:15
