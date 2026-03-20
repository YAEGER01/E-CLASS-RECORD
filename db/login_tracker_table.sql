-- Login Tracker Table for Rate Limiting
-- Run this SQL in your database (phpMyAdmin or MySQL workbench)

CREATE TABLE IF NOT EXISTS login_tracker (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    ip_address VARCHAR(45) NOT NULL,
    user_role VARCHAR(50) NOT NULL,
    attempts INT DEFAULT 0 NOT NULL,
    last_attempt_at BIGINT NOT NULL,
    is_blocked TINYINT(1) DEFAULT 0 NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);