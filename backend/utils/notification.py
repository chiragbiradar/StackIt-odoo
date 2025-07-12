import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import List

from py_pg_notify import Listener, Notifier
from py_pg_notify import Notification as PGNotification
from sqlalchemy import text
from sqlalchemy.orm import Session

from database.models import Answer, NotificationType, Question, User
from database.models import Notification as NotificationModel

# Database configuration - using environment variables for now
# You can replace these with your config system
user = os.environ.get("DBUSER", "postgres")
password = os.environ.get("DBPASS", "1234")
host = os.environ.get("DBHOST", "localhost")
port = int(os.environ.get("DBPORT", "5432"))
db = os.environ.get("DBNAME", "stackit_db")

# Constants
CONTENT_PREVIEW_LENGTH = 100

logger = logging.getLogger(__name__)

class StackItNotificationService:
    """Simplified StackIt notification service using PostgreSQL only."""

    def __init__(self):
        # Simple PostgreSQL-only approach
        pass

    async def initialize(self):
        """Initialize the notification service with triggers and listeners."""
        try:
            # Set up database triggers for automatic notifications
            await self.setup_notification_triggers()

            # Start listening for notifications
            await self.start_listening()

            logger.info("StackIt notification service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize notification service: {e}")
            # Don't raise - allow the service to continue without notifications
            logger.warning("Continuing without real-time notifications")

    async def setup_notification_triggers(self):
        """Set up PostgreSQL triggers for StackIt notifications."""
        try:
            async with Notifier(self.pg_config) as notifier:
                # Create trigger functions (ignore if already exist)
                try:
                    await notifier.create_trigger_function(
                        "notify_answer_to_question",
                        "stackit_answer_notifications"
                    )
                except Exception as e:
                    if "already exists" not in str(e):
                        raise
                    logger.info("Trigger function notify_answer_to_question already exists")

                try:
                    await notifier.create_trigger_function(
                        "notify_comment_on_answer",
                        "stackit_comment_notifications"
                    )
                except Exception as e:
                    if "already exists" not in str(e):
                        raise
                    logger.info("Trigger function notify_comment_on_answer already exists")

                try:
                    await notifier.create_trigger_function(
                        "notify_mention",
                        "stackit_mention_notifications"
                    )
                except Exception as e:
                    if "already exists" not in str(e):
                        raise
                    logger.info("Trigger function notify_mention already exists")

                # Create triggers (ignore if already exist)
                try:
                    await notifier.create_trigger(
                        table_name="answers",
                        trigger_name="answer_notification_trigger",
                        function_name="notify_answer_to_question",
                        event="INSERT"
                    )
                except Exception as e:
                    if "already exists" not in str(e):
                        raise
                    logger.info("Trigger answer_notification_trigger already exists")

                try:
                    await notifier.create_trigger(
                        table_name="comments",
                        trigger_name="comment_notification_trigger",
                        function_name="notify_comment_on_answer",
                        event="INSERT"
                    )
                except Exception as e:
                    if "already exists" not in str(e):
                        raise
                    logger.info("Trigger comment_notification_trigger already exists")

                logger.info("Notification triggers set up successfully")
        except Exception as e:
            logger.error(f"Error setting up notification triggers: {e}")
            # Don't raise - continue without triggers

    async def start_listening(self):
        """Start listening for PostgreSQL notifications."""
        try:
            # Create and store the listener
            self.listener = Listener(self.pg_config)

            # Connect the listener first
            await self.listener.connect()

            # Add listeners for different notification types
            await self.listener.add_listener("stackit_answer_notifications", self.handle_answer_notification)
            await self.listener.add_listener("stackit_comment_notifications", self.handle_comment_notification)
            await self.listener.add_listener("stackit_mention_notifications", self.handle_mention_notification)

            logger.info("Started listening for StackIt notifications")
        except Exception as e:
            logger.error(f"Error starting notification listener: {e}")
            # Don't raise - continue without listener

    async def handle_answer_notification(self, msg: PGNotification):
        """Handle answer notifications."""
        try:
            payload = json.loads(msg.payload) if msg.payload else {}
            logger.info(f"Answer notification received: {payload}")
            # Notifications are stored directly in database by helper functions

        except Exception as e:
            logger.error(f"Error handling answer notification: {e}")

    async def handle_comment_notification(self, msg: PGNotification):
        """Handle comment notifications."""
        try:
            payload = json.loads(msg.payload) if msg.payload else {}
            logger.info(f"Comment notification received: {payload}")
            # Notifications are stored directly in database by helper functions

        except Exception as e:
            logger.error(f"Error handling comment notification: {e}")

    async def handle_mention_notification(self, msg: PGNotification):
        """Handle mention notifications."""
        try:
            payload = json.loads(msg.payload) if msg.payload else {}
            logger.info(f"Mention notification received: {payload}")
            # Notifications are stored directly in database by helper functions

        except Exception as e:
            logger.error(f"Error handling mention notification: {e}")

# Removed store_notification method - notifications are stored directly in database by helper functions

    def get_notifications(self, username: str, db: Session) -> List[dict]:
        """Get all notifications for a user by username from PostgreSQL."""
        try:
            # Get user by username
            user = db.query(User).filter(User.username == username).first()
            if not user:
                return []

            # Get notifications from database with error handling
            try:

                # Use raw SQL to avoid enum conversion issues
                result_proxy = db.execute(text("""
                    SELECT id, title, message, notification_type, user_id,
                           triggered_by_user_id, related_question_id, related_answer_id,
                           related_comment_id, is_read, created_at, updated_at
                    FROM notifications
                    WHERE user_id = :user_id
                    ORDER BY created_at DESC
                """), {"user_id": user.id})

                notifications = result_proxy.fetchall()

            except Exception as e:
                logger.error(f"Database query error: {e}")
                return []

            # Convert to dict format with robust enum handling
            result = []
            for row in notifications:
                try:
                    # Handle raw SQL result - notification_type is now a string
                    notification_type_str = row.notification_type
                    logger.debug(f"Processing notification {row.id}, type: {notification_type_str}")

                    # Convert lowercase database value to uppercase display value
                    type_mapping = {
                        "mention": "MENTION",
                        "answer_to_question": "ANSWER_TO_QUESTION",
                        "comment_on_answer": "COMMENT_ON_ANSWER",
                        "answer_accepted": "ANSWER_ACCEPTED",
                        "vote_received": "VOTE_RECEIVED"
                    }
                    type_str = type_mapping.get(notification_type_str, str(notification_type_str).upper())

                    # Handle timestamp conversion safely
                    if hasattr(row.created_at, 'isoformat'):
                        timestamp = row.created_at.isoformat()
                    else:
                        # If it's already a string, use it as is
                        timestamp = str(row.created_at)

                    result.append({
                        "id": row.id,
                        "type": type_str,
                        "title": row.title,
                        "message": row.message,
                        "read": row.is_read,
                        "timestamp": timestamp,
                        "triggered_by_user_id": row.triggered_by_user_id,
                        "related_question_id": row.related_question_id,
                        "related_answer_id": row.related_answer_id,
                        "related_comment_id": row.related_comment_id
                    })

                except Exception as enum_error:
                    logger.error(f"Error processing notification {row.id}: {enum_error}")
                    # Skip this notification but continue with others
                    continue

            return result

        except Exception as e:
            logger.error(f"Error getting notifications for user {username}: {e}")
            return []

    def mark_notification_as_read(self, username: str, notification_id: int, db: Session) -> bool:
        """Mark a specific notification as read in PostgreSQL."""
        try:
            # Get user by username
            user = db.query(User).filter(User.username == username).first()
            if not user:
                return False

            # Update notification
            notification = db.query(NotificationModel).filter(
                NotificationModel.id == notification_id,
                NotificationModel.user_id == user.id
            ).first()

            if notification:
                notification.is_read = True
                notification.updated_at = datetime.now(timezone.utc)
                db.commit()
                return True
            return False

        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            db.rollback()
            return False

    def mark_all_notifications_as_read(self, username: str, db: Session) -> int:
        """Mark all notifications as read for a user in PostgreSQL."""
        try:
            # Get user by username
            user = db.query(User).filter(User.username == username).first()
            if not user:
                return 0

            # Update all unread notifications
            count = db.query(NotificationModel).filter(
                NotificationModel.user_id == user.id,
                ~NotificationModel.is_read
            ).update({
                'is_read': True,
                'updated_at': datetime.now(timezone.utc)
            })
            db.commit()
            return count

        except Exception as e:
            logger.error(f"Error marking all notifications as read: {e}")
            db.rollback()
            return 0

    def remove_notification(self, username: str, notification_id: int, db: Session):
        """Remove a specific notification from PostgreSQL."""
        try:
            # Get user by username
            user = db.query(User).filter(User.username == username).first()
            if not user:
                return

            # Delete notification
            notification = db.query(NotificationModel).filter(
                NotificationModel.id == notification_id,
                NotificationModel.user_id == user.id
            ).first()

            if notification:
                db.delete(notification)
                db.commit()

        except Exception as e:
            logger.error(f"Error removing notification: {e}")
            db.rollback()

    def remove_all_notifications(self, username: str, db: Session):
        """Remove all notifications for a user from PostgreSQL."""
        try:
            # Get user by username
            user = db.query(User).filter(User.username == username).first()
            if not user:
                return

            # Delete all notifications
            db.query(NotificationModel).filter(
                NotificationModel.user_id == user.id
            ).delete()
            db.commit()

        except Exception as e:
            logger.error(f"Error removing all notifications: {e}")
            db.rollback()

    async def send_custom_notification(self, channel: str, payload: dict):
        """Send a custom notification to a specific channel."""
        try:
            async with Notifier(self.pg_config) as notifier:
                # Ensure payload is properly escaped for PostgreSQL
                payload_str = json.dumps(payload, ensure_ascii=True)
                logger.debug(f"Sending notification to {channel}: {payload_str}")
                await notifier.notify(channel, payload_str)
                logger.info(f"Sent custom notification to {channel}")
        except Exception as e:
            logger.error(f"Error sending custom notification to {channel}: {e}")
            logger.error(f"Payload was: {payload}")
            # Continue without failing - store in cache only

    async def close(self):
        """Close the notification service."""
        try:
            if self.listener:
                await self.listener.disconnect()
            logger.info("Notification service closed")
        except Exception as e:
            logger.error(f"Error closing notification service: {e}")

# Helper functions for StackIt-specific notifications
def extract_mentions(content: str) -> List[str]:
    """Extract @username mentions from content."""
    pattern = r'@(\w+)'
    return re.findall(pattern, content)

async def create_database_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    notification_type: NotificationType,
    **kwargs
) -> NotificationModel:
    """Create a notification in the database."""
    try:
        notification = NotificationModel(
            title=title,
            message=message,
            notification_type=notification_type,
            user_id=user_id,
            triggered_by_user_id=kwargs.get('triggered_by_user_id'),
            related_question_id=kwargs.get('related_question_id'),
            related_answer_id=kwargs.get('related_answer_id'),
            related_comment_id=kwargs.get('related_comment_id'),
            is_read=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        db.add(notification)
        db.commit()
        db.refresh(notification)

        return notification

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating database notification: {e}")
        raise


# Global notification service instance
notification_service = StackItNotificationService()

# API functions for backward compatibility and easy integration
def get_user_notifications(username: str, db: Session) -> dict:
    """Get all notifications for a user by username."""
    try:
        notifications = notification_service.get_notifications(username, db)
        return {
            "notifications": notifications,
            "count": len(notifications),
            "unread_count": len([n for n in notifications if not n.get("read", False)])
        }
    except Exception as e:
        logger.error(f"Error getting user notifications: {e}")
        return {"error": "Failed to get notifications"}

def mark_notification_as_read(username: str, notification_id: int, db: Session) -> dict:
    """Mark a specific notification as read."""
    try:
        success = notification_service.mark_notification_as_read(username, notification_id, db)
        if success:
            return {"msg": "Notification marked as read"}
        else:
            return {"error": "Notification not found"}
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        return {"error": "Failed to mark notification as read"}

def mark_all_notifications_as_read(username: str, db: Session) -> dict:
    """Mark all notifications as read for a user."""
    try:
        count = notification_service.mark_all_notifications_as_read(username, db)
        return {"msg": f"Marked {count} notifications as read"}
    except Exception as e:
        logger.error(f"Error marking all notifications as read: {e}")
        return {"error": "Failed to mark notifications as read"}

# StackIt-specific notification helper functions
async def notify_answer_to_question(db: Session, question_id: int, answer_author_id: int):
    """Send notification when someone answers a question."""
    try:
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question or question.author_id == answer_author_id:
            return  # Don't notify if question not found or self-answer

        answer_author = db.query(User).filter(User.id == answer_author_id).first()
        if not answer_author:
            return

        # Create database notification
        await create_database_notification(
            db=db,
            user_id=question.author_id,
            title="New Answer to Your Question",
            message=f"{answer_author.username} answered your question: {question.title}",
            notification_type=NotificationType.ANSWER_TO_QUESTION,
            triggered_by_user_id=answer_author_id,
            related_question_id=question_id
        )

        # Get question author email
        question_author = db.query(User).filter(User.id == question.author_id).first()
        if not question_author:
            return

        # Notification is already stored in database by create_database_notification above
        logger.info(f"Answer notification sent to {question_author.username}")

    except Exception as e:
        logger.error(f"Error sending answer notification: {e}")

async def notify_comment_on_answer(db: Session, answer_id: int, comment_author_id: int):
    """Send notification when someone comments on an answer."""
    try:
        answer = db.query(Answer).filter(Answer.id == answer_id).first()
        if not answer or answer.author_id == comment_author_id:
            return  # Don't notify if answer not found or self-comment

        comment_author = db.query(User).filter(User.id == comment_author_id).first()
        if not comment_author:
            return

        # Create database notification
        await create_database_notification(
            db=db,
            user_id=answer.author_id,
            title="New Comment on Your Answer",
            message=f"{comment_author.username} commented on your answer",
            notification_type=NotificationType.COMMENT_ON_ANSWER,
            triggered_by_user_id=comment_author_id,
            related_answer_id=answer_id
        )

        # Get answer author email
        answer_author = db.query(User).filter(User.id == answer.author_id).first()
        if not answer_author:
            return

        # Send real-time notification
        await notification_service.send_custom_notification(
            "stackit_comment_notifications",
            {
                "username": answer_author.username,
                "type": "comment_on_answer",
                "title": "New Comment on Your Answer",
                "message": f"{comment_author.username} commented on your answer",
                "triggered_by": comment_author.username,
                "answer_id": answer_id
            }
        )

    except Exception as e:
        logger.error(f"Error sending comment notification: {e}")

async def notify_mention(
    db: Session,
    mentioned_username: str,
    mentioning_user_id: int,
    content: str,
    **related_ids
):
    """Send notification when someone mentions a user with @username."""
    try:
        mentioned_user = db.query(User).filter(User.username == mentioned_username).first()
        if not mentioned_user or mentioned_user.id == mentioning_user_id:
            return  # Don't notify if user not found or self-mention

        mentioning_user = db.query(User).filter(User.id == mentioning_user_id).first()
        if not mentioning_user:
            return

        # Create database notification
        await create_database_notification(
            db=db,
            user_id=mentioned_user.id,
            title="You Were Mentioned",
            message=f"{mentioning_user.username} mentioned you in a post",
            notification_type=NotificationType.MENTION,
            triggered_by_user_id=mentioning_user_id,
            **related_ids
        )

        await notification_service.send_custom_notification(
            "stackit_mention_notifications",
            {
                "username": mentioned_user.username,
                "type": "mention",
                "title": "You Were Mentioned",
                "message": f"{mentioning_user.username} mentioned you",
                "triggered_by": mentioning_user.username,
                "question_id": related_ids.get('related_question_id'),
                "answer_id": related_ids.get('related_answer_id'),
                "comment_id": related_ids.get('related_comment_id')
            }
        )

    except Exception as e:
        logger.error(f"Error sending mention notification: {e}")

# Initialize the notification service (call this when starting the application)
async def initialize_notification_service():
    """Initialize the notification service. Call this on application startup."""
    try:
        await notification_service.initialize()
        logger.info("StackIt notification service started successfully")
    except Exception as e:
        logger.error(f"Failed to start notification service: {e}")
        raise

# Cleanup function (call this when shutting down the application)
async def cleanup_notification_service():
    """Cleanup the notification service. Call this on application shutdown."""
    try:
        await notification_service.close()
        logger.info("StackIt notification service stopped successfully")
    except Exception as e:
        logger.error(f"Error stopping notification service: {e}")
