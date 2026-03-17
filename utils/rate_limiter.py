"""
Login Rate Limiter Module

This module provides rate limiting functionality for login endpoints.
It tracks failed login attempts and temporarily blocks users after
exceeding the maximum number of attempts.
"""

import time
import logging
from utils.db_conn import get_db_connection

logger = logging.getLogger(__name__)


class LoginLimiter:
    """
    Rate limiter for login endpoints.
    """

    def __init__(self):
        self.attempts_limit = 5
        self.lock_duration = 240  # Countdown duration in seconds. Edit this value (e.g., 240 = 4 minutes).

    def _get_db(self):
        return get_db_connection()

    def _ensure_table_exists(self):
        """Ensure the login_tracker table exists."""
        try:
            db = self._get_db()
            cursor = db.cursor()

            # Check if table exists
            cursor.execute(
                """
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
                )
            """
            )
            db.commit()
            cursor.close()
            logger.info("login_tracker table verified/created successfully")
        except Exception as e:
            logger.error(f"Error creating login_tracker table: {str(e)}")

    def is_blocked(self, username, ip_address):
        """Check if a user/IP combination is currently blocked."""
        try:
            self._ensure_table_exists()

            db = self._get_db()
            cursor = db.cursor()
            now = int(time.time())

            cursor.execute(
                "SELECT attempts, is_blocked, last_attempt_at FROM login_tracker WHERE username = %s AND ip_address = %s",
                (username, ip_address),
            )
            result = cursor.fetchone()
            cursor.close()

            if not result:
                return False, 0

            if not result["is_blocked"]:  # is_blocked
                return False, 0

            last_attempt = result["last_attempt_at"]
            time_passed = now - last_attempt

            if time_passed >= self.lock_duration:
                self._reset_attempts(username, ip_address)
                return False, 0

            remaining = self.lock_duration - time_passed
            return True, remaining

        except Exception as e:
            logger.error(f"Error checking block status: {type(e).__name__}: {str(e)}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return False, 0

    def _reset_attempts(self, username, ip_address):
        """Reset failed attempts after lock expires."""
        try:
            db = self._get_db()
            cursor = db.cursor()
            cursor.execute(
                "DELETE FROM login_tracker WHERE username = %s AND ip_address = %s",
                (username, ip_address),
            )
            db.commit()
            cursor.close()
        except Exception as e:
            logger.error(f"Error resetting attempts: {str(e)}")

    def process_fail(self, username, ip_address, user_role):
        """Record a failed login attempt."""
        try:
            self._ensure_table_exists()

            db = self._get_db()
            cursor = db.cursor()
            now = int(time.time())

            # Check if record exists
            cursor.execute(
                "SELECT attempts FROM login_tracker WHERE username = %s AND ip_address = %s",
                (username, ip_address),
            )
            existing = cursor.fetchone()

            if existing:
                new_attempts = existing["attempts"] + 1
                is_blocked = 1 if new_attempts >= self.attempts_limit else 0
                logger.debug(
                    f"Updating attempts for {username}: {existing['attempts']} -> {new_attempts}, is_blocked={is_blocked}"
                )
                cursor.execute(
                    """
                    UPDATE login_tracker 
                    SET attempts = %s, last_attempt_at = %s, is_blocked = %s
                    WHERE username = %s AND ip_address = %s
                """,
                    (new_attempts, now, is_blocked, username, ip_address),
                )
            else:
                logger.debug(f"Inserting new record for {username}")
                cursor.execute(
                    """
                    INSERT INTO login_tracker (username, ip_address, user_role, attempts, last_attempt_at, is_blocked)
                    VALUES (%s, %s, %s, 1, %s, 0)
                """,
                    (username, ip_address, user_role, now),
                )

            db.commit()
            cursor.close()

            if existing:
                attempts_after = existing["attempts"] + 1
                if attempts_after >= self.attempts_limit:
                    logger.warning(
                        f"User {username} ({ip_address}) blocked due to {attempts_after} failed attempts"
                    )

        except Exception as e:
            logger.error(f"Error processing failed login: {type(e).__name__}: {str(e)}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")

    def process_success(self, username, ip_address):
        """Reset failed attempts on successful login."""
        try:
            db = self._get_db()
            cursor = db.cursor()
            cursor.execute(
                "DELETE FROM login_tracker WHERE username = %s AND ip_address = %s",
                (username, ip_address),
            )
            db.commit()
            cursor.close()
            logger.info(f"Reset failed attempts for user {username}")
        except Exception as e:
            logger.error(f"Error resetting attempts on success: {str(e)}")

    def check_rate_limit(self, username, ip_address):
        """Check if user is rate limited before processing login."""
        is_blocked, remaining = self.is_blocked(username, ip_address)

        if is_blocked:
            minutes = remaining // 60
            seconds = remaining % 60
            message = (
                f"Too many failed attempts. Please try again in {minutes}m {seconds}s"
            )
            return False, message, remaining

        return True, "", 0


_limiter_instance = None


def get_login_limiter():
    """Get or create the global LoginLimiter instance."""
    global _limiter_instance
    if _limiter_instance is None:
        _limiter_instance = LoginLimiter()
    return _limiter_instance
