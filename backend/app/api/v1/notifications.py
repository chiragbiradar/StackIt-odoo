"""
Notification management API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, asc, and_
from typing import Optional, List
import logging

from ...database import get_db
from ...models.notification import Notification, NotificationType
from ...models.user import User
from ...schemas.notification import (
    NotificationResponse, NotificationList, NotificationUpdate,
    NotificationSummary, BulkNotificationUpdate, NotificationFilter
)
from ...schemas.common import (
    PaginationParams, PaginatedResponse, MessageResponse
)
from ...auth.dependencies import require_auth

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=PaginatedResponse[NotificationList])
async def list_notifications(
    pagination: PaginationParams = Depends(),
    is_read: Optional[bool] = Query(None, description="Filter by read status"),
    notification_type: Optional[NotificationType] = Query(None, description="Filter by type"),
    sort_by: str = Query("created_at", description="Sort field"),
    order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of current user's notifications.
    
    - **page**: Page number (default: 1)
    - **size**: Items per page (default: 20, max: 100)
    - **is_read**: Filter by read status (true/false)
    - **notification_type**: Filter by notification type
    - **sort_by**: Sort field (created_at)
    - **order**: Sort order (asc, desc)
    """
    query = db.query(Notification).options(
        joinedload(Notification.triggered_by_user)
    ).filter(Notification.user_id == current_user.id)
    
    # Apply filters
    if is_read is not None:
        query = query.filter(Notification.is_read == is_read)
    
    if notification_type:
        query = query.filter(Notification.notification_type == notification_type)
    
    # Apply sorting
    sort_column = getattr(Notification, sort_by, Notification.created_at)
    if order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    notifications = query.offset(pagination.offset).limit(pagination.size).all()
    
    return PaginatedResponse.create(
        items=notifications,
        total=total,
        page=pagination.page,
        size=pagination.size
    )


@router.get("/summary", response_model=NotificationSummary)
async def get_notification_summary(
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Get notification summary for current user.
    
    Returns unread count, recent notifications, and type breakdown.
    """
    # Get unread count
    unread_count = db.query(Notification).filter(
        and_(
            Notification.user_id == current_user.id,
            Notification.is_read == False
        )
    ).count()
    
    # Get recent notifications (last 10)
    recent_notifications = db.query(Notification).options(
        joinedload(Notification.triggered_by_user)
    ).filter(
        Notification.user_id == current_user.id
    ).order_by(desc(Notification.created_at)).limit(10).all()
    
    # Get notification type counts
    type_counts = {}
    for notification_type in NotificationType:
        count = db.query(Notification).filter(
            and_(
                Notification.user_id == current_user.id,
                Notification.notification_type == notification_type,
                Notification.is_read == False
            )
        ).count()
        type_counts[notification_type.value] = count
    
    return NotificationSummary(
        unread_count=unread_count,
        recent_notifications=recent_notifications,
        notification_types_count=type_counts
    )


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: int,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Get notification details by ID.
    
    - **notification_id**: Notification ID to retrieve
    
    Only returns notifications belonging to the current user.
    """
    notification = db.query(Notification).options(
        joinedload(Notification.triggered_by_user)
    ).filter(
        and_(
            Notification.id == notification_id,
            Notification.user_id == current_user.id
        )
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    return notification


@router.put("/{notification_id}", response_model=NotificationResponse)
async def update_notification(
    notification_id: int,
    notification_update: NotificationUpdate,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Update a notification (mark as read/unread).
    
    - **notification_id**: Notification ID to update
    - **is_read**: Mark as read (true) or unread (false)
    
    Only the notification owner can update their notifications.
    """
    notification = db.query(Notification).filter(
        and_(
            Notification.id == notification_id,
            Notification.user_id == current_user.id
        )
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    # Update read status
    notification.is_read = notification_update.is_read
    
    db.commit()
    db.refresh(notification)
    
    logger.info(f"Notification {notification_id} marked as {'read' if notification_update.is_read else 'unread'} by {current_user.username}")
    
    return notification


@router.post("/mark-all-read", response_model=MessageResponse)
async def mark_all_notifications_read(
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Mark all notifications as read for current user.
    """
    updated_count = db.query(Notification).filter(
        and_(
            Notification.user_id == current_user.id,
            Notification.is_read == False
        )
    ).update({"is_read": True})
    
    db.commit()
    
    logger.info(f"Marked {updated_count} notifications as read for {current_user.username}")
    
    return MessageResponse(
        message=f"Marked {updated_count} notifications as read",
        success=True
    )


@router.post("/bulk-update", response_model=MessageResponse)
async def bulk_update_notifications(
    bulk_update: BulkNotificationUpdate,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Bulk update multiple notifications.
    
    - **notification_ids**: List of notification IDs to update
    - **is_read**: Mark as read (true) or unread (false)
    
    Only updates notifications belonging to the current user.
    """
    # Verify all notifications belong to current user
    notifications = db.query(Notification).filter(
        and_(
            Notification.id.in_(bulk_update.notification_ids),
            Notification.user_id == current_user.id
        )
    ).all()
    
    if len(notifications) != len(bulk_update.notification_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Some notifications not found or don't belong to you"
        )
    
    # Update notifications
    updated_count = db.query(Notification).filter(
        and_(
            Notification.id.in_(bulk_update.notification_ids),
            Notification.user_id == current_user.id
        )
    ).update({"is_read": bulk_update.is_read})
    
    db.commit()
    
    action = "read" if bulk_update.is_read else "unread"
    logger.info(f"Bulk marked {updated_count} notifications as {action} for {current_user.username}")
    
    return MessageResponse(
        message=f"Updated {updated_count} notifications",
        success=True
    )


@router.delete("/{notification_id}", response_model=MessageResponse)
async def delete_notification(
    notification_id: int,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Delete a notification.
    
    - **notification_id**: Notification ID to delete
    
    Only the notification owner can delete their notifications.
    """
    notification = db.query(Notification).filter(
        and_(
            Notification.id == notification_id,
            Notification.user_id == current_user.id
        )
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    # Delete notification
    db.delete(notification)
    db.commit()
    
    logger.info(f"Notification deleted by {current_user.username}: {notification_id}")
    
    return MessageResponse(
        message="Notification deleted successfully",
        success=True
    )
