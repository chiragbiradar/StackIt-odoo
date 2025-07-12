"""
User management API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from typing import Optional, List
import logging

from ...database import get_db
from ...models.user import User
from ...schemas.user import (
    UserResponse, UserUpdate, UserList, UserProfile, UserStats,
    PasswordChange
)
from ...schemas.common import (
    PaginationParams, PaginatedResponse, MessageResponse
)
from ...auth.dependencies import (
    get_current_active_user, require_admin, check_resource_ownership
)
from ...auth.password import hash_password, verify_password
from ...auth.utils import get_user_permissions, get_user_badges, calculate_user_level

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=PaginatedResponse[UserList])
async def list_users(
    pagination: PaginationParams = Depends(),
    search: Optional[str] = Query(None, description="Search users by username or full name"),
    sort_by: str = Query("created_at", description="Sort field"),
    order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of users.
    
    - **page**: Page number (default: 1)
    - **size**: Items per page (default: 20, max: 100)
    - **search**: Search term for username or full name
    - **sort_by**: Sort field (created_at, username, reputation_score)
    - **order**: Sort order (asc, desc)
    """
    query = db.query(User).filter(User.is_active == True)
    
    # Apply search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (User.username.ilike(search_term)) |
            (User.full_name.ilike(search_term))
        )
    
    # Apply sorting
    sort_column = getattr(User, sort_by, User.created_at)
    if order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    users = query.offset(pagination.offset).limit(pagination.size).all()
    
    return PaginatedResponse.create(
        items=users,
        total=total,
        page=pagination.page,
        size=pagination.size
    )


@router.get("/me", response_model=UserProfile)
async def get_my_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's detailed profile.
    
    Returns extended profile information including permissions and badges.
    """
    # Get user permissions
    permissions = get_user_permissions(current_user)
    
    # Get user badges
    badges = get_user_badges(current_user, db)
    
    # Get user level
    level_info = calculate_user_level(current_user)
    
    # Create profile response
    profile = UserProfile.model_validate(current_user)
    profile.badges = [badge["name"] for badge in badges]

    return profile


@router.put("/me", response_model=UserResponse)
async def update_my_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile.
    
    - **full_name**: Updated full name
    - **bio**: Updated biography
    - **avatar_url**: Updated avatar URL
    """
    # Update user fields
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    
    if user_update.bio is not None:
        current_user.bio = user_update.bio
    
    if user_update.avatar_url is not None:
        current_user.avatar_url = user_update.avatar_url
    
    db.commit()
    db.refresh(current_user)
    
    logger.info(f"User profile updated: {current_user.username}")
    
    return current_user


@router.post("/me/change-password", response_model=MessageResponse)
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Change current user's password.
    
    - **current_password**: Current password for verification
    - **new_password**: New password
    - **confirm_password**: New password confirmation
    """
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    current_user.hashed_password = hash_password(password_data.new_password)
    db.commit()
    
    logger.info(f"Password changed for user: {current_user.username}")
    
    return MessageResponse(
        message="Password changed successfully",
        success=True
    )


@router.get("/{user_id}", response_model=UserProfile)
async def get_user_profile(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get user profile by ID.
    
    - **user_id**: User ID to retrieve
    
    Returns public profile information for the specified user.
    """
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get user badges (public information)
    badges = get_user_badges(user, db)
    
    # Create profile response
    profile = UserProfile.model_validate(user)
    profile.badges = [badge["name"] for badge in badges]

    return profile


@router.get("/{user_id}/stats", response_model=UserStats)
async def get_user_stats(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get user statistics.
    
    - **user_id**: User ID to get statistics for
    
    Returns detailed statistics about the user's activity.
    """
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Calculate additional statistics
    from ...models.answer import Answer
    from ...models.vote import Vote
    
    # Get accepted answers count
    accepted_answers = db.query(Answer).filter(
        Answer.author_id == user_id,
        Answer.is_accepted == True
    ).count()
    
    # Get total votes received
    total_votes = db.query(Vote).join(Answer).filter(
        Answer.author_id == user_id
    ).count()
    
    # Get badges count
    badges = get_user_badges(user, db)
    
    return UserStats(
        total_questions=user.questions_count,
        total_answers=user.answers_count,
        total_votes_received=total_votes,
        accepted_answers=accepted_answers,
        reputation_score=user.reputation_score,
        badges_earned=len(badges),
        join_date=user.created_at,
        last_active=user.updated_at
    )


@router.delete("/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Delete a user account (Admin only).
    
    - **user_id**: User ID to delete
    
    This is a soft delete - the user is marked as inactive.
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Soft delete - mark as inactive
    user.is_active = False
    db.commit()
    
    logger.info(f"User deleted by admin {current_user.username}: {user.username}")
    
    return MessageResponse(
        message=f"User {user.username} has been deactivated",
        success=True
    )
