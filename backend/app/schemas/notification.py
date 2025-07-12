"""
Notification-related Pydantic schemas.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

from ..models.notification import NotificationType
from .common import BaseResponseModel
from .user import UserList


class NotificationBase(BaseModel):
    """Base notification schema with common fields."""
    
    title: str = Field(max_length=200, description="Notification title")
    message: str = Field(description="Notification message content")
    notification_type: NotificationType = Field(description="Type of notification")


class NotificationResponse(BaseResponseModel):
    """Schema for notification responses."""
    
    title: str
    message: str
    notification_type: NotificationType
    is_read: bool
    user_id: int
    triggered_by_user_id: Optional[int]
    related_question_id: Optional[int]
    related_answer_id: Optional[int]
    related_comment_id: Optional[int]
    
    # Related data
    triggered_by_user: Optional[UserList]
    
    model_config = ConfigDict(from_attributes=True)


class NotificationList(BaseModel):
    """Schema for notification list items."""
    
    id: int
    title: str
    message: str
    notification_type: NotificationType
    is_read: bool
    created_at: datetime
    
    # Related data
    triggered_by_user: Optional[UserList]
    
    model_config = ConfigDict(from_attributes=True)


class NotificationUpdate(BaseModel):
    """Schema for notification updates."""
    
    is_read: bool = Field(description="Mark notification as read/unread")


class NotificationCreate(NotificationBase):
    """Schema for notification creation (internal use)."""
    
    user_id: int = Field(description="ID of user to notify")
    triggered_by_user_id: Optional[int] = Field(default=None, description="ID of user who triggered notification")
    related_question_id: Optional[int] = Field(default=None, description="Related question ID")
    related_answer_id: Optional[int] = Field(default=None, description="Related answer ID")
    related_comment_id: Optional[int] = Field(default=None, description="Related comment ID")


class NotificationSettings(BaseModel):
    """User notification preferences schema."""
    
    email_notifications: bool = Field(default=True, description="Enable email notifications")
    push_notifications: bool = Field(default=True, description="Enable push notifications")
    answer_notifications: bool = Field(default=True, description="Notify when someone answers my questions")
    comment_notifications: bool = Field(default=True, description="Notify when someone comments on my answers")
    mention_notifications: bool = Field(default=True, description="Notify when someone mentions me")
    vote_notifications: bool = Field(default=False, description="Notify when someone votes on my content")
    acceptance_notifications: bool = Field(default=True, description="Notify when my answer is accepted")


class NotificationStats(BaseModel):
    """Notification statistics schema."""
    
    total_notifications: int = Field(description="Total notifications")
    unread_notifications: int = Field(description="Unread notifications")
    notifications_today: int = Field(description="Notifications received today")
    notifications_this_week: int = Field(description="Notifications received this week")
    most_common_type: NotificationType = Field(description="Most common notification type")
    last_notification: Optional[datetime] = Field(description="Timestamp of last notification")


class NotificationSummary(BaseModel):
    """Notification summary for dashboard."""
    
    unread_count: int = Field(description="Number of unread notifications")
    recent_notifications: List[NotificationList] = Field(description="Recent notifications")
    notification_types_count: dict = Field(description="Count by notification type")


class BulkNotificationUpdate(BaseModel):
    """Schema for bulk notification operations."""
    
    notification_ids: List[int] = Field(min_items=1, description="List of notification IDs")
    is_read: bool = Field(description="Mark as read/unread")


class NotificationFilter(BaseModel):
    """Schema for notification filtering."""
    
    is_read: Optional[bool] = Field(default=None, description="Filter by read status")
    notification_type: Optional[NotificationType] = Field(default=None, description="Filter by type")
    date_from: Optional[datetime] = Field(default=None, description="Filter from date")
    date_to: Optional[datetime] = Field(default=None, description="Filter to date")
    triggered_by_user_id: Optional[int] = Field(default=None, description="Filter by triggering user")
    sort_by: str = Field(default="created_at", description="Sort field")
    order: str = Field(default="desc", regex="^(asc|desc)$", description="Sort order")
