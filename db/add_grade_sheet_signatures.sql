-- Migration: Add grade_sheet_signatures table
-- This table stores customizable signature information for grade sheet reports

CREATE TABLE IF NOT EXISTS `grade_sheet_signatures` (
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
