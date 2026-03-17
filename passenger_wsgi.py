"""
Passenger WSGI file for cPanel Python App deployment
This file is the entry point for your Flask application on cPanel hosting.
"""

import sys
import os

# Get the path to the Python interpreter in the virtual environment
# Note: Update this path to match your cPanel virtual environment path
INTERP = os.path.expanduser("~/virtualenv/public_html/3.9/bin/python3")

# Use the virtual environment Python if not already using it
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

# Add your project directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

# Change to project directory
os.chdir(os.path.dirname(__file__))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Import your Flask application
# The 'application' variable name is required by Passenger
from app import app as application

# Optional: Enable debugging in development (disable in production)
# application.debug = False

# Log startup
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Passenger WSGI application started")
logger.info(f"Python version: {sys.version}")
logger.info(f"Working directory: {os.getcwd()}")
logger.info(f"FLASK_ENV: {os.getenv('FLASK_ENV', 'not set')}")
logger.info(f"PRODUCTION_DOMAIN: {os.getenv('PRODUCTION_DOMAIN', 'not set')}")
