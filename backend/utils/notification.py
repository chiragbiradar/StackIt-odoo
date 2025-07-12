import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import List

from diskcache import Cache
from py_pg_notify import Listener, Notifier, PGConfig
from py_pg_notify import Notification as PGNotification
from sqlalchemy.orm import Session

from database.models import Answer, Question, User
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
    """StackIt notification service using py-pg-notify for real-time notifications."""

    def __init__(self):
        self.cache = Cache(directory=os.getenv("CACHE_DIR", "./cache"))
        self.expire = 259200  # 3 days
        self.pg_config = PGConfig(
            user=user,
            password=password,
            host=host,
            port=port,
            dbname=db
        )
        self.listener = None
        self.notifier = None

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

            # Store in cache for retrieval
            await self.store_notification(payload, "answer_to_question")

        except Exception as e:
            logger.error(f"Error handling answer notification: {e}")

    async def handle_comment_notification(self, msg: PGNotification):
        """Handle comment notifications."""
        try:
            payload = json.loads(msg.payload) if msg.payload else {}
            logger.info(f"Comment notification received: {payload}")

            # Store in cache for retrieval
            await self.store_notification(payload, "comment_on_answer")

        except Exception as e:
            logger.error(f"Error handling comment notification: {e}")

    async def handle_mention_notification(self, msg: PGNotification):
        """Handle mention notifications."""
        try:
            payload = json.loads(msg.payload) if msg.payload else {}
            logger.info(f"Mention notification received: {payload}")

            # Store in cache for retrieval
            await self.store_notification(payload, "mention")

        except Exception as e:
            logger.error(f"Error handling mention notification: {e}")

    async def store_notification(self, payload: dict, notification_type: str):
        """Store notification in cache and database."""
        try:
            user_email = payload.get("user_email")
            if not user_email:
                return

            # Create unique key for cache using email
            notification_id = f"{user_email}_{notification_type}_{payload.get('id', '')}"

            # Store in cache
            self.cache.set(
                notification_id,
                value={
                    "type": notification_type,
                    "payload": payload,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "read": False
                },
                expire=self.expire
            )

            logger.info(f"Stored notification for user {user_email}: {notification_type}")

        except Exception as e:
            logger.error(f"Error storing notification: {e}")

    def get_notifications(self, user_email: str) -> List[dict]:
        """Get all notifications for a user by email."""
        try:
            notifications = []
            keys = list(self.cache.iterkeys())

            for key in keys:
                if user_email in key:
                    notification = self.cache.get(key)
                    if notification:
                        notifications.append(notification)

            # Sort by timestamp (newest first)
            notifications.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            return notifications

        except Exception as e:
            logger.error(f"Error getting notifications for user {user_email}: {e}")
            return []

    def mark_notification_as_read(self, user_email: str, notification_id: str) -> bool:
        """Mark a specific notification as read."""
        try:
            cache_key = f"{user_email}_{notification_id}"
            notification = self.cache.get(cache_key)

            if notification:
                notification["read"] = True
                self.cache.set(cache_key, notification, expire=self.expire)
                return True
            return False

        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            return False

    def mark_all_notifications_as_read(self, user_email: str) -> int:
        """Mark all notifications as read for a user."""
        try:
            count = 0
            keys = list(self.cache.iterkeys())

            for key in keys:
                if user_email in key:
                    notification = self.cache.get(key)
                    if notification and not notification.get("read", False):
                        notification["read"] = True
                        self.cache.set(key, notification, expire=self.expire)
                        count += 1

            return count

        except Exception as e:
            logger.error(f"Error marking all notifications as read: {e}")
            return 0

    def remove_notification(self, user_email: str, notification_id: str):
        """Remove a specific notification."""
        try:
            cache_key = f"{user_email}_{notification_id}"
            if self.cache.get(cache_key):
                del self.cache[cache_key]
        except Exception as e:
            logger.error(f"Error removing notification: {e}")

    def remove_all_notifications(self, user_email: str):
        """Remove all notifications for a user."""
        try:
            keys = list(self.cache.iterkeys())
            for key in keys:
                if user_email in key:
                    del self.cache[key]
        except Exception as e:
            logger.error(f"Error removing all notifications: {e}")

    async def send_custom_notification(self, channel: str, payload: dict):
        """Send a custom notification to a specific channel."""
        try:
            async with Notifier(self.pg_config) as notifier:
                await notifier.notify(channel, json.dumps(payload))
                logger.info(f"Sent custom notification to {channel}")
        except Exception as e:
            logger.error(f"Error sending custom notification: {e}")

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
    notification_type: str,
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
def get_user_notifications(user_email: str) -> dict:
    """Get all notifications for a user by email."""
    try:
        notifications = notification_service.get_notifications(user_email)
        return {
            "notifications": notifications,
            "count": len(notifications),
            "unread_count": len([n for n in notifications if not n.get("read", False)])
        }
    except Exception as e:
        logger.error(f"Error getting user notifications: {e}")
        return {"error": "Failed to get notifications"}

def mark_notification_as_read(user_email: str, notification_id: str) -> dict:
    """Mark a specific notification as read."""
    try:
        success = notification_service.mark_notification_as_read(user_email, notification_id)
        if success:
            return {"msg": "Notification marked as read"}
        else:
            return {"error": "Notification not found"}
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        return {"error": "Failed to mark notification as read"}

def mark_all_notifications_as_read(user_email: str) -> dict:
    """Mark all notifications as read for a user."""
    try:
        count = notification_service.mark_all_notifications_as_read(user_email)
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
            notification_type="answer_to_question",
            triggered_by_user_id=answer_author_id,
            related_question_id=question_id
        )

        # Get question author email
        question_author = db.query(User).filter(User.id == question.author_id).first()
        if not question_author:
            return

        # Send real-time notification
        await notification_service.send_custom_notification(
            "stackit_answer_notifications",
            {
                "user_email": question_author.email,
                "type": "answer_to_question",
                "title": "New Answer to Your Question",
                "message": f"{answer_author.username} answered your question: {question.title}",
                "triggered_by": answer_author.username,
                "question_id": question_id,
                "question_title": question.title
            }
        )

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
            notification_type="comment_on_answer",
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
                "user_email": answer_author.email,
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
            notification_type="mention",
            triggered_by_user_id=mentioning_user_id,
            **related_ids
        )

        # Send real-time notification
        await notification_service.send_custom_notification(
            "stackit_mention_notifications",
            {
                "user_email": mentioned_user.email,
                "type": "mention",
                "title": "You Were Mentioned",
                "message": f"{mentioning_user.username} mentioned you in a post",
                "triggered_by": mentioning_user.username,
                "content_preview": content[:CONTENT_PREVIEW_LENGTH] + "..." if len(content) > CONTENT_PREVIEW_LENGTH else content,
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
