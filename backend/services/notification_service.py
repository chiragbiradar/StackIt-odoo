"""
Notification Service for StackIt Q&A platform.
Handles real-time notifications using py-pg-notify.
"""

from fastapi import APIRouter, Depends, HTTPException, status

# Import database dependencies
from database.models import User

# Import auth dependencies
from services.auth_service import get_current_user_dependency
from utils.notification import (
    get_user_notifications,
    mark_all_notifications_as_read,
    mark_notification_as_read,
    notification_service,
)

# Create router
router = APIRouter()


@router.get("/")
async def get_notifications(
    current_user: User = Depends(get_current_user_dependency)
):
    """
    Get all notifications for the current user.

    Returns:
    - List of notifications with read/unread status
    - Total count and unread count
    """
    try:
        result = get_user_notifications(current_user.email)
        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching notifications: {str(e)}"
        ) from e


@router.post("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user_dependency)
):
    """
    Mark a specific notification as read.

    Args:
    - notification_id: ID of the notification to mark as read
    """
    try:
        result = mark_notification_as_read(current_user.email, notification_id)
        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error marking notification as read: {str(e)}"
        ) from e


@router.post("/read-all")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user_dependency)
):
    """
    Mark all notifications as read for the current user.
    """
    try:
        result = mark_all_notifications_as_read(current_user.email)
        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error marking all notifications as read: {str(e)}"
        ) from e


@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user_dependency)
):
    """
    Get the count of unread notifications for the current user.

    Returns:
    - unread_count: Number of unread notifications
    """
    try:
        result = get_user_notifications(current_user.email)
        return {"unread_count": result.get("unread_count", 0)}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting unread count: {str(e)}"
        ) from e


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user_dependency)
):
    """
    Delete a specific notification.

    Args:
    - notification_id: ID of the notification to delete
    """
    try:
        notification_service.remove_notification(current_user.email, notification_id)
        return {"msg": "Notification deleted successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting notification: {str(e)}"
        ) from e


@router.delete("/")
async def delete_all_notifications(
    current_user: User = Depends(get_current_user_dependency)
):
    """
    Delete all notifications for the current user.
    """
    try:
        notification_service.remove_all_notifications(current_user.email)
        return {"msg": "All notifications deleted successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting all notifications: {str(e)}"
        ) from e
