import os
import logging
import threading
from typing import Optional
from flask import Flask
from dotenv import load_dotenv

# Configure logging for database operations
logger = logging.getLogger(__name__)

# Hardcoded credentials.
# WARNING: These are secrets stored in source. Do NOT commit to public repos.
HARDCODE_ENVIRONMENT = "online"
HARDCODE_ONLINE_DB_HOST = "localhost"
HARDCODE_ONLINE_DB_NAME = "Issuedclassrecord_e_class_record"
HARDCODE_ONLINE_DB_PORT = 3306
HARDCODE_ONLINE_DB_PASSWORD = "Disguisedtoast1234!"
HARDCODE_ONLINE_DB_USER = "Issuedclassrecord_142joe"
HARDCODE_SECRET_KEY = "dev-secret-key-change-in-production"


class DatabaseConnection:
    """Handles database connection, initialization, and management."""

    def __init__(self, app: Optional[Flask] = None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask):
        """Initialize database connection with Flask app."""
        # Load environment variables
        load_dotenv()
        logger.info("Environment variables loaded from .env file")

        # Determine database configuration based on environment
        # Use hardcoded ENVIRONMENT as default (overridable by actual env)
        environment = os.getenv("ENVIRONMENT", HARDCODE_ENVIRONMENT).lower()
        logger.info(f"Database environment: {environment}")

        if environment == "local":
            db_host = os.getenv("LOCAL_DB_HOST")
            db_port = os.getenv("LOCAL_DB_PORT")
            db_user = os.getenv("LOCAL_DB_USER")
            db_password = os.getenv("LOCAL_DB_PASSWORD")
            db_name = os.getenv("LOCAL_DB_NAME")
        elif environment == "production" or environment == "online":
            # Prefer environment variables, fall back to hardcoded values
            db_host = os.getenv("ONLINE_DB_HOST", HARDCODE_ONLINE_DB_HOST)
            db_port = os.getenv("ONLINE_DB_PORT", str(HARDCODE_ONLINE_DB_PORT))
            db_user = os.getenv("ONLINE_DB_USER", HARDCODE_ONLINE_DB_USER)
            db_password = os.getenv("ONLINE_DB_PASSWORD", HARDCODE_ONLINE_DB_PASSWORD)
            db_name = os.getenv("ONLINE_DB_NAME", HARDCODE_ONLINE_DB_NAME)
        else:
            raise ValueError(
                f"Invalid ENVIRONMENT value: {environment}. Must be 'local' or 'production'/'online'"
            )

        # Database configuration
        db_uri = (
            f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        )
        app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        # Ensure SECRET_KEY is set on the app (hardcoded default)
        app.config.setdefault(
            "SECRET_KEY", os.getenv("SECRET_KEY", HARDCODE_SECRET_KEY)
        )

        # Connection pool settings to handle connection timeouts
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_size": 10,  # Number of connections to maintain
            "max_overflow": 20,  # Additional connections beyond pool_size
            "pool_recycle": 3600,  # Recycle connections after 1 hour
            "pool_pre_ping": True,  # Test connections before use
            "pool_timeout": 30,  # Connection timeout in seconds
            "connect_args": {
                "connect_timeout": 30,  # Connection timeout for initial connection
                "read_timeout": 60,  # Read timeout
                "write_timeout": 30,  # Write timeout
            },
        }
        logger.info(
            f"Database URI configured for {environment}: {db_uri.replace(db_password or '', '***')}"
        )

        # Check if SQLAlchemy is already registered with this app
        if not hasattr(app, "extensions") or "sqlalchemy" not in app.extensions:
            # Initialize database with app only if not already registered
            db.init_app(app)
            logger.info("Database initialized with Flask app")
        else:
            logger.info(
                "Database already initialized with Flask app - skipping re-initialization"
            )

    def test_connection(self) -> bool:
        """Test database connection with retry mechanism."""
        if self.app is None:
            logger.error("Database connection not initialized with Flask app")
            return False

        max_retries = 3
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                logger.info(
                    f"Testing database connection... (attempt {attempt + 1}/{max_retries})"
                )
                with self.app.app_context():
                    with db.engine.connect() as connection:
                        connection.execute(db.text("SELECT 1"))
                logger.info("✅ Database connection successful!")
                return True
            except Exception as e:
                logger.warning(
                    f"❌ Database connection failed (attempt {attempt + 1}): {str(e)}"
                )
                if attempt < max_retries - 1:
                    import time

                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(
                        f"❌ Database connection failed after {max_retries} attempts: {str(e)}"
                    )
                    return False

    def create_tables(self) -> bool:
        """Create all database tables."""
        if self.app is None:
            logger.error("Database connection not initialized with Flask app")
            return False
        try:
            logger.info("Creating database tables...")
            with self.app.app_context():
                db.create_all()
            logger.info("✅ Database tables created successfully!")
            return True
        except Exception as e:
            logger.error(f"❌ Database table creation failed: {str(e)}")
            return False

    def init_database(self) -> bool:
        """Initialize database connection and create tables if they don't exist."""
        logger.info("Starting database initialization...")

        if not self.test_connection():
            return False

        if not self.create_tables():
            return False

        return True

    def get_db(self):
        """Get database instance."""
        return db

    def ensure_connection(self) -> bool:
        """Ensure database connection is available, attempt to reconnect if needed."""
        try:
            with self.app.app_context():
                with db.engine.connect() as connection:
                    connection.execute(db.text("SELECT 1"))
            return True
        except Exception as e:
            logger.warning(
                f"Database connection lost, attempting to reconnect: {str(e)}"
            )
            try:
                # Dispose of the current engine to force recreation of connections
                db.engine.dispose()
                # Test the connection again
                return self.test_connection()
            except Exception as reconnect_error:
                logger.error(f"Failed to reconnect to database: {str(reconnect_error)}")
                return False


# Global database connection instance
db_conn = DatabaseConnection()


def init_database_with_app(app: Flask) -> bool:
    """Initialize database with Flask app and return success status."""
    global db_conn
    db_conn = DatabaseConnection(app)
    return db_conn.init_database()


# Use a thread-local container so each thread/request gets its own PyMySQL connection
_local = threading.local()


def _get_thread_conn():
    return getattr(_local, "_connection", None)


def _set_thread_conn(conn):
    setattr(_local, "_connection", conn)


def get_db_connection():
    """Get PyMySQL database connection for current thread. Create if not exists or reconnect if lost.

    Returns a connection object that is safe to use within the current thread. This avoids sharing
    a single global connection across concurrent requests which can lead to "Packet sequence" errors.
    """
    conn = _get_thread_conn()
    if conn is None or not _is_connection_alive(conn):
        try:
            # Close existing connection if present
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
                _set_thread_conn(None)

            # Load environment variables
            load_dotenv()
            logger.info("Environment variables loaded from .env file")

            # Determine database configuration based on environment
            environment = os.getenv("ENVIRONMENT", HARDCODE_ENVIRONMENT).lower()
            logger.info(f"Database environment: {environment}")

            if environment == "local":
                db_host = os.getenv("LOCAL_DB_HOST", "localhost")
                db_port = int(os.getenv("LOCAL_DB_PORT", "3307"))
                db_user = os.getenv("LOCAL_DB_USER", "root")
                db_password = os.getenv("LOCAL_DB_PASSWORD", "new_password")
                db_name = os.getenv("LOCAL_DB_NAME", "e_class_record")
            elif environment == "production" or environment == "online":
                db_host = os.getenv("ONLINE_DB_HOST", HARDCODE_ONLINE_DB_HOST)
                db_port = int(os.getenv("ONLINE_DB_PORT", str(HARDCODE_ONLINE_DB_PORT)))
                db_user = os.getenv("ONLINE_DB_USER", HARDCODE_ONLINE_DB_USER)
                db_password = os.getenv(
                    "ONLINE_DB_PASSWORD", HARDCODE_ONLINE_DB_PASSWORD
                )
                db_name = os.getenv("ONLINE_DB_NAME", HARDCODE_ONLINE_DB_NAME)
            else:
                raise ValueError(
                    f"Invalid ENVIRONMENT value: {environment}. Must be 'local' or 'production'/'online'"
                )

            # Import PyMySQL lazily
            import pymysql

            conn = pymysql.connect(
                host=db_host,
                port=db_port,
                user=db_user,
                password=db_password,
                database=db_name,
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False,
            )
            _set_thread_conn(conn)
            logger.info(
                f"PyMySQL database connection established for {environment} (thread-local)"
            )
        except Exception as e:
            logger.error(f"PyMySQL database connection failed: {str(e)}")
            raise e
    return _get_thread_conn()


def _is_connection_alive(conn):
    """Check if the provided connection is alive"""
    if conn is None:
        return False
    try:
        conn.ping(reconnect=False)
        return True
    except Exception:
        return False


def close_db_connection():
    """Close and remove the thread-local PyMySQL connection, if present."""
    try:
        conn = _get_thread_conn()
        if conn:
            try:
                conn.close()
            except Exception:
                pass
            _set_thread_conn(None)
            logger.info("Thread-local DB connection closed")
    except Exception as e:
        logger.warning(f"Error closing thread-local DB connection: {e}")
