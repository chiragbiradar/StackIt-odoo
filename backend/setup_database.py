#!/usr/bin/env python3
"""
Comprehensive database setup script for StackIt application.
Automates the entire database setup process from scratch.
"""
import sys
import os
import subprocess
import time
from pathlib import Path

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

import logging
from app.config import settings
from app.database import check_database_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_command(command, description, check=True):
    """Run a shell command with logging."""
    logger.info(f"Running: {description}")
    logger.debug(f"Command: {command}")
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=check, 
            capture_output=True, 
            text=True
        )
        
        if result.stdout:
            logger.debug(f"stdout: {result.stdout}")
        if result.stderr:
            logger.warning(f"stderr: {result.stderr}")
            
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {e}")
        if e.stdout:
            logger.error(f"stdout: {e.stdout}")
        if e.stderr:
            logger.error(f"stderr: {e.stderr}")
        return False


def check_prerequisites():
    """Check if all prerequisites are installed."""
    logger.info("Checking prerequisites...")
    
    prerequisites = [
        ("python", "Python 3.8+"),
        ("pip", "Python package manager"),
        ("psql", "PostgreSQL client"),
        ("docker", "Docker (optional)"),
        ("docker-compose", "Docker Compose (optional)")
    ]
    
    missing = []
    for cmd, desc in prerequisites:
        if not run_command(f"which {cmd}", f"Checking {desc}", check=False):
            if cmd in ["docker", "docker-compose"]:
                logger.warning(f"⚠️  {desc} not found (optional)")
            else:
                missing.append(desc)
                logger.error(f"❌ {desc} not found")
        else:
            logger.info(f"✅ {desc} found")
    
    if missing:
        logger.error("Missing required prerequisites. Please install:")
        for item in missing:
            logger.error(f"  - {item}")
        return False
    
    return True


def install_python_dependencies():
    """Install Python dependencies."""
    logger.info("Installing Python dependencies...")
    
    if not run_command("pip install -r requirements.txt", "Installing requirements"):
        logger.error("Failed to install Python dependencies")
        return False
    
    logger.info("✅ Python dependencies installed successfully")
    return True


def setup_docker_database():
    """Set up database using Docker."""
    logger.info("Setting up database with Docker...")
    
    # Check if Docker is available
    if not run_command("docker --version", "Checking Docker", check=False):
        logger.error("Docker not available")
        return False
    
    # Start PostgreSQL container
    if not run_command(
        "docker-compose up -d postgres", 
        "Starting PostgreSQL container"
    ):
        logger.error("Failed to start PostgreSQL container")
        return False
    
    # Wait for database to be ready
    logger.info("Waiting for database to be ready...")
    max_attempts = 30
    for attempt in range(max_attempts):
        if check_database_connection():
            logger.info("✅ Database is ready")
            return True
        
        logger.info(f"Attempt {attempt + 1}/{max_attempts}: Database not ready, waiting...")
        time.sleep(2)
    
    logger.error("Database failed to start within timeout")
    return False


def setup_local_database():
    """Set up database on local PostgreSQL installation."""
    logger.info("Setting up local PostgreSQL database...")
    
    # Create database and user
    commands = [
        f"createdb {settings.db_name}",
        f"psql -c \"CREATE USER {settings.db_user} WITH PASSWORD '{settings.db_password}';\"",
        f"psql -c \"GRANT ALL PRIVILEGES ON DATABASE {settings.db_name} TO {settings.db_user};\""
    ]
    
    for cmd in commands:
        if not run_command(cmd, f"Executing: {cmd}", check=False):
            logger.warning(f"Command may have failed (database/user might already exist): {cmd}")
    
    # Test connection
    if check_database_connection():
        logger.info("✅ Local database setup successful")
        return True
    else:
        logger.error("❌ Local database setup failed")
        return False


def run_migrations():
    """Run database migrations."""
    logger.info("Running database migrations...")
    
    # Generate initial migration if needed
    if not run_command(
        "python manage_db.py generate-migration -m 'Initial schema'",
        "Generating initial migration",
        check=False
    ):
        logger.info("Migration generation skipped (may already exist)")
    
    # Apply migrations
    if not run_command("python manage_db.py migrate", "Applying migrations"):
        logger.error("Failed to apply migrations")
        return False
    
    logger.info("✅ Migrations applied successfully")
    return True


def seed_database():
    """Seed database with initial data."""
    logger.info("Seeding database with initial data...")
    
    if not run_command("python manage_db.py seed-data", "Seeding database"):
        logger.error("Failed to seed database")
        return False
    
    logger.info("✅ Database seeded successfully")
    return True


def setup_optimizations():
    """Set up database optimizations."""
    logger.info("Setting up database optimizations...")
    
    if not run_command("python manage_db.py setup-optimizations", "Setting up optimizations"):
        logger.error("Failed to set up optimizations")
        return False
    
    logger.info("✅ Database optimizations set up successfully")
    return True


def run_tests():
    """Run database tests."""
    logger.info("Running database tests...")
    
    if not run_command("python test_database.py --manual", "Running manual tests"):
        logger.error("Manual tests failed")
        return False
    
    # Try to run pytest tests if pytest is available
    if run_command("which pytest", "Checking pytest", check=False):
        if not run_command("python test_database.py --pytest", "Running pytest tests"):
            logger.warning("Pytest tests failed")
    else:
        logger.info("Pytest not available, skipping pytest tests")
    
    logger.info("✅ Database tests completed")
    return True


def create_env_file():
    """Create .env file if it doesn't exist."""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        logger.info("Creating .env file from .env.example...")
        env_file.write_text(env_example.read_text())
        logger.info("✅ .env file created")
        logger.warning("⚠️  Please review and update .env file with your settings")
    elif not env_file.exists():
        logger.warning("⚠️  No .env file found. Please create one with your database settings")


def main():
    """Main setup function."""
    logger.info("🚀 Starting StackIt database setup...")
    
    # Check prerequisites
    if not check_prerequisites():
        logger.error("❌ Prerequisites check failed")
        sys.exit(1)
    
    # Create .env file
    create_env_file()
    
    # Install Python dependencies
    if not install_python_dependencies():
        logger.error("❌ Failed to install dependencies")
        sys.exit(1)
    
    # Set up database (try Docker first, then local)
    database_ready = False
    
    # Try Docker setup
    if run_command("docker --version", "Checking Docker", check=False):
        logger.info("Docker available, trying Docker setup...")
        if setup_docker_database():
            database_ready = True
        else:
            logger.warning("Docker setup failed, trying local setup...")
    
    # Try local setup if Docker failed or not available
    if not database_ready:
        logger.info("Trying local PostgreSQL setup...")
        if setup_local_database():
            database_ready = True
    
    if not database_ready:
        logger.error("❌ Failed to set up database")
        logger.error("Please ensure PostgreSQL is installed and running")
        sys.exit(1)
    
    # Run migrations
    if not run_migrations():
        logger.error("❌ Migration setup failed")
        sys.exit(1)
    
    # Seed database
    if not seed_database():
        logger.error("❌ Database seeding failed")
        sys.exit(1)
    
    # Set up optimizations
    if not setup_optimizations():
        logger.warning("⚠️  Database optimizations setup failed (non-critical)")
    
    # Run tests
    if not run_tests():
        logger.warning("⚠️  Some tests failed (non-critical)")
    
    logger.info("🎉 StackIt database setup completed successfully!")
    logger.info("")
    logger.info("Next steps:")
    logger.info("1. Review the .env file and update settings if needed")
    logger.info("2. Start your FastAPI application")
    logger.info("3. Check the DATABASE_README.md for usage instructions")
    logger.info("")
    logger.info("Database management commands:")
    logger.info("  python manage_db.py --help")
    logger.info("")
    logger.info("Test the setup:")
    logger.info("  python manage_db.py check-connection")
    logger.info("  python manage_db.py info")


if __name__ == "__main__":
    main()
