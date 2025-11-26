-- Migration: Add audit_logs table for tracking admin actions
-- Date: 2025-11-25

CREATE TABLE IF NOT EXISTS `audit_logs` (
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
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- Insert initial audit log entry for migration
INSERT INTO
    `audit_logs` (
        `admin_id`,
        `admin_school_id`,
        `action`,
        `resource_type`,
        `details`
    )
SELECT id, school_id, 'SYSTEM_MIGRATION', 'database', 'Added audit_logs table for admin action tracking'
FROM users
WHERE
    role = 'admin'
LIMIT 1;