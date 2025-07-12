"""
Authentication dependencies for FastAPI endpoints.
"""
from typing import Optional, Callable
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..models.user import User, UserRole
from ..database import get_db
from .jwt import get_current_active_user


def require_auth(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Require authentication for an endpoint.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current user object
    """
    return current_user


def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Require admin role for an endpoint.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current user object
        
    Raises:
        HTTPException: If user is not an admin
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return current_user


def require_role(required_role: UserRole) -> Callable:
    """
    Create a dependency that requires a specific role.
    
    Args:
        required_role: Required user role
        
    Returns:
        Dependency function
    """
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role != required_role and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role.value}' required"
            )
        return current_user
    
    return role_checker


def require_owner_or_admin(resource_owner_id: int) -> Callable:
    """
    Create a dependency that requires the user to be the owner of a resource or an admin.
    
    Args:
        resource_owner_id: ID of the resource owner
        
    Returns:
        Dependency function
    """
    def owner_or_admin_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.id != resource_owner_id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only access your own resources"
            )
        return current_user
    
    return owner_or_admin_checker


def check_resource_ownership(
    resource_owner_id: int,
    current_user: User,
    allow_admin: bool = True
) -> bool:
    """
    Check if the current user owns a resource or is an admin.
    
    Args:
        resource_owner_id: ID of the resource owner
        current_user: Current authenticated user
        allow_admin: Whether to allow admin access
        
    Returns:
        True if user has access, False otherwise
    """
    if current_user.id == resource_owner_id:
        return True
    
    if allow_admin and current_user.is_admin:
        return True
    
    return False


def require_verified_user(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Require a verified user for an endpoint.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current user object
        
    Raises:
        HTTPException: If user is not verified
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required"
        )
    
    return current_user


def optional_auth(
    current_user: Optional[User] = Depends(get_current_active_user)
) -> Optional[User]:
    """
    Optional authentication dependency.
    Returns user if authenticated, None otherwise.
    
    Args:
        current_user: Current authenticated user (optional)
        
    Returns:
        Current user object or None
    """
    return current_user


class PermissionChecker:
    """Class for checking user permissions on resources."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def can_edit_question(self, question_id: int, user: User) -> bool:
        """Check if user can edit a question."""
        from ..models.question import Question
        
        question = self.db.query(Question).filter(Question.id == question_id).first()
        if not question:
            return False
        
        return user.id == question.author_id or user.is_admin
    
    def can_delete_question(self, question_id: int, user: User) -> bool:
        """Check if user can delete a question."""
        return self.can_edit_question(question_id, user)
    
    def can_edit_answer(self, answer_id: int, user: User) -> bool:
        """Check if user can edit an answer."""
        from ..models.answer import Answer
        
        answer = self.db.query(Answer).filter(Answer.id == answer_id).first()
        if not answer:
            return False
        
        return user.id == answer.author_id or user.is_admin
    
    def can_delete_answer(self, answer_id: int, user: User) -> bool:
        """Check if user can delete an answer."""
        return self.can_edit_answer(answer_id, user)
    
    def can_accept_answer(self, answer_id: int, user: User) -> bool:
        """Check if user can accept an answer."""
        from ..models.answer import Answer
        
        answer = self.db.query(Answer).filter(Answer.id == answer_id).first()
        if not answer:
            return False
        
        # Only question author or admin can accept answers
        return user.id == answer.question.author_id or user.is_admin
    
    def can_vote_on_answer(self, answer_id: int, user: User) -> bool:
        """Check if user can vote on an answer."""
        from ..models.answer import Answer
        
        answer = self.db.query(Answer).filter(Answer.id == answer_id).first()
        if not answer:
            return False
        
        # Users cannot vote on their own answers
        return user.id != answer.author_id
    
    def can_edit_comment(self, comment_id: int, user: User) -> bool:
        """Check if user can edit a comment."""
        from ..models.comment import Comment
        
        comment = self.db.query(Comment).filter(Comment.id == comment_id).first()
        if not comment:
            return False
        
        return user.id == comment.author_id or user.is_admin
    
    def can_delete_comment(self, comment_id: int, user: User) -> bool:
        """Check if user can delete a comment."""
        return self.can_edit_comment(comment_id, user)


def get_permission_checker(db: Session = Depends(get_db)) -> PermissionChecker:
    """Get permission checker instance."""
    return PermissionChecker(db)
