-- MFA Trusted Devices Table
-- Run this migration to add MFA trusted devices functionality

CREATE TABLE IF NOT EXISTS mfa_trusted_devices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    role ENUM(
        'admin',
        'instructor',
        'student'
    ) NOT NULL,
    device_fingerprint VARCHAR(128) NOT NULL,
    ip_address VARCHAR(45) NOT NULL,
    user_agent_hash VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_device_fingerprint (device_fingerprint),
    INDEX idx_expires_at (expires_at),
    UNIQUE KEY unique_device_per_user (user_id, device_fingerprint)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- Clean up expired trusted devices periodically (optional - can be run as a scheduled task)
-- DELETE FROM mfa_trusted_devices WHERE expires_at < NOW();