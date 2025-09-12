import os
import logging
from flask import Flask
from dotenv import load_dotenv
from models import db

# Configure logging for database operations
logger = logging.getLogger(__name__)

class DatabaseConnection:
    """Handles database connection, initialization, and management."""

    def __init__(self, app: Flask = None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask):
        """Initialize database connection with Flask app."""
        # Load environment variables
        load_dotenv()
        logger.info("Environment variables loaded from .env file")

        # Database configuration
        db_uri = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
        app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        logger.info(f"Database URI configured: {db_uri.replace(os.getenv('DB_PASSWORD'), '***')}")

        # Initialize database with app
        db.init_app(app)
        logger.info("Database initialized with Flask app")

    def test_connection(self) -> bool:
        """Test database connection."""
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