import os
import logging
from typing import Optional
from flask import Flask
from dotenv import load_dotenv
from models import db

# Configure logging for database operations
logger = logging.getLogger(__name__)

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
        environment = os.getenv('ENVIRONMENT', 'local').lower()
        logger.info(f"Database environment: {environment}")

        if environment == 'local':
            db_host = os.getenv('LOCAL_DB_HOST')
            db_port = os.getenv('LOCAL_DB_PORT')
            db_user = os.getenv('LOCAL_DB_USER')
            db_password = os.getenv('LOCAL_DB_PASSWORD')
            db_name = os.getenv('LOCAL_DB_NAME')
        elif environment == 'production' or environment == 'online':
            db_host = os.getenv('ONLINE_DB_HOST')
            db_port = os.getenv('ONLINE_DB_PORT')
            db_user = os.getenv('ONLINE_DB_USER')
            db_password = os.getenv('ONLINE_DB_PASSWORD')
            db_name = os.getenv('ONLINE_DB_NAME')
        else:
            raise ValueError(f"Invalid ENVIRONMENT value: {environment}. Must be 'local' or 'production'/'online'")

        # Database configuration
        db_uri = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        logger.info(f"Database URI configured for {environment}: {db_uri.replace(db_password or '', '***')}")

        # Check if SQLAlchemy is already registered with this app
        if not hasattr(app, 'extensions') or 'sqlalchemy' not in app.extensions:
            # Initialize database with app only if not already registered
            db.init_app(app)
            logger.info("Database initialized with Flask app")
        else:
            logger.info("Database already initialized with Flask app - skipping re-initialization")

    def test_connection(self) -> bool:
        """Test database connection."""
        if self.app is None:
            logger.error("Database connection not initialized with Flask app")
            return False
        try:
            logger.info("Testing database connection...")
            with self.app.app_context():
                with db.engine.connect() as connection:
                    connection.execute(db.text('SELECT 1'))
            logger.info("✅ Database connection successful!")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {str(e)}")
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

# Global database connection instance
db_conn = DatabaseConnection()

def init_database_with_app(app: Flask) -> bool:
    """Initialize database with Flask app and return success status."""
    global db_conn
    db_conn = DatabaseConnection(app)
    return db_conn.init_database()