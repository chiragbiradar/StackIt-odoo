"""
Comment management API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, asc
from typing import Optional
import logging

from ...database import get_db
from ...models.comment import Comment
from ...models.answer import Answer
from ...models.user import User
from ...schemas.comment import (
    CommentCreate, CommentUpdate, CommentResponse, CommentList, CommentDetail
)
from ...schemas.common import (
    PaginationParams, PaginatedResponse, MessageResponse
)
from ...auth.dependencies import (
    require_auth, get_permission_checker, get_current_active_user
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=PaginatedResponse[CommentList])
async def list_comments(
    pagination: PaginationParams = Depends(),
    answer_id: Optional[int] = Query(None, description="Filter by answer ID"),
    author_id: Optional[int] = Query(None, description="Filter by author ID"),
    sort_by: str = Query("created_at", description="Sort field"),
    order: str = Query("asc", regex="^(asc|desc)$", description="Sort order"),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of comments.
    
    - **page**: Page number (default: 1)
    - **size**: Items per page (default: 20, max: 100)
    - **answer_id**: Filter by answer ID
    - **author_id**: Filter by comment author
    - **sort_by**: Sort field (created_at)
    - **order**: Sort order (asc, desc)
    """
    query = db.query(Comment).options(joinedload(Comment.author))
    
    # Apply filters
    if answer_id:
        query = query.filter(Comment.answer_id == answer_id)
    
    if author_id:
        query = query.filter(Comment.author_id == author_id)
    
    # Apply sorting
    sort_column = getattr(Comment, sort_by, Comment.created_at)
    if order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    comments = query.offset(pagination.offset).limit(pagination.size).all()
    
    return PaginatedResponse.create(
        items=comments,
        total=total,
        page=pagination.page,
        size=pagination.size
    )


@router.post("/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    comment_data: CommentCreate,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Create a new comment on an answer.
    
    - **answer_id**: ID of the answer to comment on
    - **content**: Comment content (5-500 characters)
    
    Requires authentication and email verification.
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required to post comments"
        )
    
    # Check if answer exists
    answer = db.query(Answer).filter(Answer.id == comment_data.answer_id).first()
    
    if not answer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Answer not found"
        )
    
    # Create comment
    comment = Comment(
        content=comment_data.content,
        answer_id=comment_data.answer_id,
        author_id=current_user.id
    )
    
    db.add(comment)
    
    # Update answer comment count
    answer.comment_count += 1
    
    db.commit()
    db.refresh(comment)
    
    logger.info(f"Comment created by {current_user.username} on answer {comment_data.answer_id}")
    
    return comment


@router.get("/{comment_id}", response_model=CommentDetail)
async def get_comment(
    comment_id: int,
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get comment details by ID.
    
    - **comment_id**: Comment ID to retrieve
    
    Returns detailed comment information including permissions for current user.
    """
    comment = db.query(Comment).options(
        joinedload(Comment.author),
        joinedload(Comment.answer)
    ).filter(Comment.id == comment_id).first()
    
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    # Create detailed response with permissions
    comment_detail = CommentDetail.model_validate(comment)
    
    if current_user:
        # Set permissions
        comment_detail.can_edit = (
            current_user.id == comment.author_id or current_user.is_admin
        )
        comment_detail.can_delete = (
            current_user.id == comment.author_id or current_user.is_admin
        )
        
        # Check if comment has been edited
        comment_detail.is_edited = comment.updated_at > comment.created_at
    
    return comment_detail


@router.put("/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: int,
    comment_update: CommentUpdate,
    current_user: User = Depends(require_auth),
    permission_checker = Depends(get_permission_checker),
    db: Session = Depends(get_db)
):
    """
    Update a comment.
    
    - **comment_id**: Comment ID to update
    - **content**: Updated content (optional)
    
    Only the comment author or admins can update comments.
    """
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    # Check permissions
    if not permission_checker.can_edit_comment(comment_id, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to edit this comment"
        )
    
    # Update fields
    if comment_update.content is not None:
        comment.content = comment_update.content
    
    db.commit()
    db.refresh(comment)
    
    logger.info(f"Comment updated by {current_user.username}: {comment_id}")
    
    return comment


@router.delete("/{comment_id}", response_model=MessageResponse)
async def delete_comment(
    comment_id: int,
    current_user: User = Depends(require_auth),
    permission_checker = Depends(get_permission_checker),
    db: Session = Depends(get_db)
):
    """
    Delete a comment.
    
    - **comment_id**: Comment ID to delete
    
    Only the comment author or admins can delete comments.
    """
    comment = db.query(Comment).options(joinedload(Comment.answer)).filter(
        Comment.id == comment_id
    ).first()
    
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    # Check permissions
    if not permission_checker.can_delete_comment(comment_id, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this comment"
        )
    
    answer = comment.answer
    
    # Update answer comment count
    answer.comment_count = max(0, answer.comment_count - 1)
    
    # Delete comment
    db.delete(comment)
    db.commit()
    
    logger.info(f"Comment deleted by {current_user.username}: {comment_id}")
    
    return MessageResponse(
        message="Comment deleted successfully",
        success=True
    )
