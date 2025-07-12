#!/usr/bin/env python3
"""
Database management script for StackIt application.
Provides utilities for database operations, migrations, and seeding.
"""
import argparse
import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

from database import engine, create_tables, drop_tables, check_database_connection, get_db
from database.models.base import Base
from utils.config import settings
from database.seed_data import seed_database
from database.database_optimizations import setup_database_optimizations
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_database_tables():
    """Create all database tables."""
    try:
        logger.info("Creating database tables...")
        create_tables()
        logger.info("✅ Database tables created successfully!")
    except Exception as e:
        logger.error(f"❌ Error creating tables: {e}")
        sys.exit(1)


def drop_database_tables():
    """Drop all database tables."""
    try:
        logger.info("Dropping database tables...")
        drop_tables()
        logger.info("✅ Database tables dropped successfully!")
    except Exception as e:
        logger.error(f"❌ Error dropping tables: {e}")
        sys.exit(1)


def check_db_connection():
    """Check database connection."""
    logger.info("Checking database connection...")
    if check_database_connection():
        logger.info("✅ Database connection successful!")
    else:
        logger.error("❌ Database connection failed!")
        sys.exit(1)


def show_database_info():
    """Show database configuration information."""
    logger.info("Database Configuration:")
    logger.info(f"  Database URL: {settings.database_url}")
    logger.info(f"  Host: {settings.db_host}")
    logger.info(f"  Port: {settings.db_port}")
    logger.info(f"  Database: {settings.db_name}")
    logger.info(f"  User: {settings.db_user}")
    logger.info(f"  Environment: {settings.environment}")


def seed_database_data():
    """Seed the database with initial data."""
    try:
        logger.info("Seeding database with initial data...")
        db = next(get_db())
        seed_database(db)
        logger.info("✅ Database seeded successfully!")
    except Exception as e:
        logger.error(f"❌ Error seeding database: {e}")
        sys.exit(1)


def setup_optimizations():
    """Set up database optimizations."""
    try:
        logger.info("Setting up database optimizations...")
        db = next(get_db())
        setup_database_optimizations(db)
        logger.info("✅ Database optimizations set up successfully!")
    except Exception as e:
        logger.error(f"❌ Error setting up optimizations: {e}")
        sys.exit(1)


def run_alembic_command(command: str):
    """Run an Alembic command."""
    import subprocess
    try:
        logger.info(f"Running Alembic command: {command}")
        result = subprocess.run(f"alembic {command}", shell=True, check=True, capture_output=True, text=True)
        logger.info(result.stdout)
        if result.stderr:
            logger.warning(result.stderr)
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Alembic command failed: {e}")
        logger.error(f"stdout: {e.stdout}")
        logger.error(f"stderr: {e.stderr}")
        sys.exit(1)


def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(description="StackIt Database Management")
    parser.add_argument(
        "command",
        choices=[
            "create-tables",
            "drop-tables",
            "check-connection",
            "info",
            "seed-data",
            "setup-optimizations",
            "init-migration",
            "generate-migration",
            "migrate",
            "downgrade",
            "current",
            "history"
        ],
        help="Database management command to execute"
    )
    parser.add_argument(
        "--message", "-m",
        help="Migration message (for generate-migration command)"
    )
    parser.add_argument(
        "--revision", "-r",
        help="Revision identifier (for downgrade command)"
    )
    
    args = parser.parse_args()
    
    if args.command == "create-tables":
        create_database_tables()
    elif args.command == "drop-tables":
        drop_database_tables()
    elif args.command == "check-connection":
        check_db_connection()
    elif args.command == "info":
        show_database_info()
    elif args.command == "seed-data":
        seed_database_data()
    elif args.command == "setup-optimizations":
        setup_optimizations()
    elif args.command == "init-migration":
        run_alembic_command("init alembic")
    elif args.command == "generate-migration":
        message = args.message or "Auto-generated migration"
        run_alembic_command(f'revision --autogenerate -m "{message}"')
    elif args.command == "migrate":
        run_alembic_command("upgrade head")
    elif args.command == "downgrade":
        revision = args.revision or "-1"
        run_alembic_command(f"downgrade {revision}")
    elif args.command == "current":
        run_alembic_command("current")
    elif args.command == "history":
        run_alembic_command("history")


if __name__ == "__main__":
    main()
