"""
Database package for StackIt Q&A platform.
Contains all database-related functionality including models, connections, and utilities.
"""
from .database import (
    SessionLocal,
    check_database_connection,
    create_tables,
    drop_tables,
    engine,
    get_db,
)
from .models.answer import Answer
from .models.base import Base
from .models.comment import Comment
from .models.notification import Notification
from .models.question import Question
from .models.tag import QuestionTag, Tag
from .models.user import User
from .models.vote import Vote

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
