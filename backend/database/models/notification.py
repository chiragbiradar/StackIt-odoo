"""
Notification model for storing user notifications.
"""
from sqlalchemy import Column, String, Text, Integer, ForeignKey, Boolean, Enum, Index
from sqlalchemy.orm import relationship
import enum

from .base import BaseModel


class NotificationType(enum.Enum):
    """Notification type enumeration."""
    ANSWER_TO_QUESTION = "answer_to_question"
    COMMENT_ON_ANSWER = "comment_on_answer"
    MENTION = "mention"
    ANSWER_ACCEPTED = "answer_accepted"
    VOTE_RECEIVED = "vote_received"


class Notification(BaseModel):
    """Notification model for storing user notifications."""
    
    __tablename__ = "notifications"
    
    # Notification content
    title = Column(
        String(200), 
        nullable=False,
        comment="Notification title"
    )
    message = Column(
        Text, 
        nullable=False,
        comment="Notification message content"
    )
    notification_type = Column(
        Enum(NotificationType), 
        nullable=False,
        comment="Type of notification"
    )
    
    # Notification status
    is_read = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether the notification has been read"
    )
    
    # Related entity references (optional, for linking to specific content)
    related_question_id = Column(
        Integer,
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=True,
        comment="Reference to related question (if applicable)"
    )
    related_answer_id = Column(
        Integer,
        ForeignKey("answers.id", ondelete="CASCADE"),
        nullable=True,
        comment="Reference to related answer (if applicable)"
    )
    related_comment_id = Column(
        Integer,
        ForeignKey("comments.id", ondelete="CASCADE"),
        nullable=True,
        comment="Reference to related comment (if applicable)"
    )
    
    # Foreign keys
    user_id = Column(
        Integer, 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False,
        index=True,
        comment="Reference to the user who should receive this notification"
    )
    triggered_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        comment="Reference to the user who triggered this notification"
    )
    
    # Relationships
    recipient = relationship("User", back_populates="received_notifications", foreign_keys=[user_id])
    triggered_by = relationship("User", back_populates="triggered_notifications", foreign_keys=[triggered_by_user_id])
    related_question = relationship("Question", foreign_keys=[related_question_id])
    related_answer = relationship("Answer", foreign_keys=[related_answer_id])
    related_comment = relationship("Comment", foreign_keys=[related_comment_id])
    
    # Table arguments for indexes and constraints
    __table_args__ = (
        # Index for user's unread notifications (most common query)
        Index('ix_notifications_user_unread', 'user_id', 'is_read', 'created_at'),
        # Index for notifications by type
        Index('ix_notifications_type_created', 'notification_type', 'created_at'),
        # Index for user's notifications ordered by creation date
        Index('ix_notifications_user_created_desc', 'user_id', 'created_at'),
    )

    def __repr__(self):
        return f"<Notification(id={self.id}, user_id={self.user_id}, type={self.notification_type.value}, is_read={self.is_read})>"

    def mark_as_read(self):
        """Mark this notification as read."""
        self.is_read = True
