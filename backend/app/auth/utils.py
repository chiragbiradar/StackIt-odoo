"""
Authentication utility functions.
"""
from typing import Dict, List, Any
from sqlalchemy.orm import Session

from ..models.user import User, UserRole


def get_user_permissions(user: User) -> Dict[str, Any]:
    """
    Get user permissions based on role and status.
    
    Args:
        user: User object
        
    Returns:
        Dictionary of user permissions
    """
    permissions = {
        "can_ask_questions": user.is_active and user.is_verified,
        "can_answer_questions": user.is_active and user.is_verified,
        "can_vote": user.is_active and user.is_verified,
        "can_comment": user.is_active and user.is_verified,
        "can_edit_own_content": user.is_active,
        "can_delete_own_content": user.is_active,
        "can_moderate": user.is_admin,
        "can_manage_users": user.is_admin,
        "can_manage_tags": user.is_admin,
        "can_view_admin_panel": user.is_admin,
        "can_access_api": user.is_active,
        "requires_verification": not user.is_verified,
        "is_admin": user.is_admin,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "role": user.role.value
    }
    
    # Add reputation-based permissions
    if user.reputation_score >= 50:
        permissions["can_vote_down"] = True
    else:
        permissions["can_vote_down"] = False
    
    if user.reputation_score >= 100:
        permissions["can_edit_others_posts"] = True
    else:
        permissions["can_edit_others_posts"] = False
    
    if user.reputation_score >= 500:
        permissions["can_close_questions"] = True
    else:
        permissions["can_close_questions"] = False
    
    return permissions


def check_rate_limit(user: User, action: str, db: Session) -> bool:
    """
    Check if user has exceeded rate limits for specific actions.
    
    Args:
        user: User object
        action: Action being performed
        db: Database session
        
    Returns:
        True if within rate limit, False otherwise
    """
    # Rate limits based on user reputation and role
    rate_limits = {
        "ask_question": {
            "new_user": 5,  # 5 questions per day for new users
            "regular_user": 20,  # 20 questions per day for regular users
            "high_rep_user": 50,  # 50 questions per day for high reputation users
            "admin": 1000  # Unlimited for admins
        },
        "post_answer": {
            "new_user": 20,
            "regular_user": 100,
            "high_rep_user": 500,
            "admin": 1000
        },
        "post_comment": {
            "new_user": 50,
            "regular_user": 200,
            "high_rep_user": 1000,
            "admin": 1000
        },
        "vote": {
            "new_user": 100,
            "regular_user": 500,
            "high_rep_user": 1000,
            "admin": 1000
        }
    }
    
    if action not in rate_limits:
        return True
    
    # Determine user category
    if user.is_admin:
        user_category = "admin"
    elif user.reputation_score >= 1000:
        user_category = "high_rep_user"
    elif user.reputation_score >= 100:
        user_category = "regular_user"
    else:
        user_category = "new_user"
    
    limit = rate_limits[action].get(user_category, 10)
    
    # TODO: Implement actual rate limiting logic with Redis or database
    # For now, return True (no rate limiting)
    return True


def get_user_badges(user: User, db: Session) -> List[Dict[str, Any]]:
    """
    Get user badges based on achievements.
    
    Args:
        user: User object
        db: Database session
        
    Returns:
        List of user badges
    """
    badges = []
    
    # Reputation badges
    if user.reputation_score >= 100:
        badges.append({
            "name": "Bronze Badge",
            "description": "Earned 100+ reputation points",
            "icon": "bronze-medal",
            "color": "#CD7F32"
        })
    
    if user.reputation_score >= 500:
        badges.append({
            "name": "Silver Badge",
            "description": "Earned 500+ reputation points",
            "icon": "silver-medal",
            "color": "#C0C0C0"
        })
    
    if user.reputation_score >= 1000:
        badges.append({
            "name": "Gold Badge",
            "description": "Earned 1000+ reputation points",
            "icon": "gold-medal",
            "color": "#FFD700"
        })
    
    # Activity badges
    if user.questions_count >= 10:
        badges.append({
            "name": "Inquisitive",
            "description": "Asked 10+ questions",
            "icon": "question-circle",
            "color": "#007bff"
        })
    
    if user.answers_count >= 10:
        badges.append({
            "name": "Helpful",
            "description": "Provided 10+ answers",
            "icon": "lightbulb",
            "color": "#28a745"
        })
    
    # Special badges
    if user.is_verified:
        badges.append({
            "name": "Verified",
            "description": "Email address verified",
            "icon": "check-circle",
            "color": "#17a2b8"
        })
    
    if user.role == UserRole.ADMIN:
        badges.append({
            "name": "Administrator",
            "description": "Site administrator",
            "icon": "shield",
            "color": "#dc3545"
        })
    
    return badges


def calculate_user_level(user: User) -> Dict[str, Any]:
    """
    Calculate user level based on reputation and activity.
    
    Args:
        user: User object
        
    Returns:
        Dictionary with level information
    """
    # Level thresholds
    levels = [
        {"level": 1, "name": "Newcomer", "min_rep": 0, "color": "#6c757d"},
        {"level": 2, "name": "Contributor", "min_rep": 50, "color": "#007bff"},
        {"level": 3, "name": "Regular", "min_rep": 200, "color": "#28a745"},
        {"level": 4, "name": "Veteran", "min_rep": 500, "color": "#ffc107"},
        {"level": 5, "name": "Expert", "min_rep": 1000, "color": "#fd7e14"},
        {"level": 6, "name": "Master", "min_rep": 2000, "color": "#e83e8c"},
        {"level": 7, "name": "Legend", "min_rep": 5000, "color": "#6f42c1"}
    ]
    
    current_level = levels[0]
    next_level = None
    
    for i, level in enumerate(levels):
        if user.reputation_score >= level["min_rep"]:
            current_level = level
            if i + 1 < len(levels):
                next_level = levels[i + 1]
        else:
            break
    
    # Calculate progress to next level
    progress = 0
    if next_level:
        current_min = current_level["min_rep"]
        next_min = next_level["min_rep"]
        progress = ((user.reputation_score - current_min) / (next_min - current_min)) * 100
        progress = min(100, max(0, progress))
    
    return {
        "current_level": current_level,
        "next_level": next_level,
        "progress_percentage": progress,
        "reputation_needed": next_level["min_rep"] - user.reputation_score if next_level else 0
    }
