"""
Database package for StackIt Q&A platform.
Contains all database-related functionality including models, connections, and utilities.
"""
from .database import engine, SessionLocal, get_db, create_tables, drop_tables, check_database_connection
from .models import *

__all__ = [
    "engine",
    "SessionLocal", 
    "get_db",
    "create_tables",
    "drop_tables",
    "check_database_connection",
    # Models
    "Base",
    "User",
    "Question", 
    "Answer",
    "Tag",
    "QuestionTag",
    "Vote",
    "Notification",
    "Comment"
]
