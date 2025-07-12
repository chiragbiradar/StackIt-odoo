"""
User model for authentication and user management.
"""
from sqlalchemy import Column, String, Boolean, Enum, Text, Integer, Index
from sqlalchemy.orm import relationship
import enum

from .base import BaseModel


class UserRole(enum.Enum):
    """User role enumeration."""
    GUEST = "guest"
    USER = "user"
    ADMIN = "admin"


class User(BaseModel):
    """User model for storing user information and authentication."""
    
    __tablename__ = "users"
    
    # Basic user information
    username = Column(
        String(50), 
        unique=True, 
        nullable=False, 
        index=True,
        comment="Unique username for the user"
    )
    email = Column(
        String(255), 
        unique=True, 
        nullable=False, 
        index=True,
        comment="User's email address"
    )
    hashed_password = Column(
        String(255), 
        nullable=False,
        comment="Hashed password for authentication"
    )
    
    # User profile information
    full_name = Column(
        String(100),
        nullable=True,
        comment="User's full name"
    )
    bio = Column(
        Text,
        nullable=True,
        comment="User's biography or description"
    )
    avatar_url = Column(
        String(500),
        nullable=True,
        comment="URL to user's avatar image"
    )
    
    # User status and role
    is_active = Column(
        Boolean, 
        default=True, 
        nullable=False,
        comment="Whether the user account is active"
    )
    is_verified = Column(
        Boolean, 
        default=False, 
        nullable=False,
        comment="Whether the user's email is verified"
    )
    role = Column(
        Enum(UserRole), 
        default=UserRole.USER, 
        nullable=False,
        comment="User's role in the system"
    )
    
    # User statistics
    reputation_score = Column(
        Integer,
        default=0,
        nullable=False,
        comment="User's reputation score based on votes received"
    )
    questions_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Total number of questions asked by the user"
    )
    answers_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Total number of answers provided by the user"
    )
    
    # Relationships
    questions = relationship(
        "Question", 
        back_populates="author", 
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    answers = relationship(
        "Answer", 
        back_populates="author", 
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    votes = relationship(
        "Vote", 
        back_populates="user", 
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    # Notifications received by this user
    received_notifications = relationship(
        "Notification",
        foreign_keys="Notification.user_id",
        back_populates="recipient",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    # Notifications triggered by this user
    triggered_notifications = relationship(
        "Notification",
        foreign_keys="Notification.triggered_by_user_id",
        back_populates="triggered_by",
        lazy="dynamic"
    )
    comments = relationship(
        "Comment", 
        back_populates="author", 
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    # Table arguments for indexes and constraints
    __table_args__ = (
        # Composite index for active users by role (for admin queries)
        Index('ix_users_active_role', 'is_active', 'role'),
        # Index for user search by username and email
        Index('ix_users_username_email', 'username', 'email'),
        # Index for reputation-based queries
        Index('ix_users_reputation_desc', 'reputation_score'),
    )

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role.value}')>"

    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role == UserRole.ADMIN

    @property
    def can_moderate(self) -> bool:
        """Check if user can moderate content."""
        return self.role == UserRole.ADMIN
