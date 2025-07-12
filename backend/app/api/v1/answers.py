"""
Answer management API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, asc
from typing import Optional
import logging

from ...database import get_db
from ...models.answer import Answer
from ...models.question import Question
from ...models.user import User
from ...schemas.answer import (
    AnswerCreate, AnswerUpdate, AnswerResponse, AnswerList,
    AnswerDetail, AnswerAccept
)
from ...schemas.common import (
    PaginationParams, PaginatedResponse, MessageResponse
)
from ...auth.dependencies import (
    get_current_active_user, require_auth, get_permission_checker
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=PaginatedResponse[AnswerList])
async def list_answers(
    pagination: PaginationParams = Depends(),
    question_id: Optional[int] = Query(None, description="Filter by question ID"),
    author_id: Optional[int] = Query(None, description="Filter by author ID"),
    is_accepted: Optional[bool] = Query(None, description="Filter by accepted status"),
    sort_by: str = Query("created_at", description="Sort field"),
    order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of answers.
    
    - **page**: Page number (default: 1)
    - **size**: Items per page (default: 20, max: 100)
    - **question_id**: Filter by question ID
    - **author_id**: Filter by answer author
    - **is_accepted**: Filter by accepted status
    - **sort_by**: Sort field (created_at, vote_score)
    - **order**: Sort order (asc, desc)
    """
    query = db.query(Answer).options(joinedload(Answer.author))
    
    # Apply filters
    if question_id:
        query = query.filter(Answer.question_id == question_id)
    
    if author_id:
        query = query.filter(Answer.author_id == author_id)
    
    if is_accepted is not None:
        query = query.filter(Answer.is_accepted == is_accepted)
    
    # Apply sorting
    sort_column = getattr(Answer, sort_by, Answer.created_at)
    if order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    answers = query.offset(pagination.offset).limit(pagination.size).all()
    
    return PaginatedResponse.create(
        items=answers,
        total=total,
        page=pagination.page,
        size=pagination.size
    )


@router.post("/", response_model=AnswerResponse, status_code=status.HTTP_201_CREATED)
async def create_answer(
    answer_data: AnswerCreate,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Create a new answer.
    
    - **question_id**: ID of the question being answered
    - **content**: Answer content in rich text (minimum 20 characters)
    
    Requires authentication and email verification.
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required to post answers"
        )
    
    # Check if question exists and is not closed
    question = db.query(Question).filter(Question.id == answer_data.question_id).first()
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    if question.is_closed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot answer a closed question"
        )
    
    # Create answer
    answer = Answer(
        content=answer_data.content,
        question_id=answer_data.question_id,
        author_id=current_user.id
    )
    
    db.add(answer)
    
    # Update question answer count
    question.answer_count += 1
    
    # Update user answer count
    current_user.answers_count += 1
    
    db.commit()
    db.refresh(answer)
    
    logger.info(f"Answer created by {current_user.username} for question {question.id}")
    
    return answer


@router.get("/{answer_id}", response_model=AnswerDetail)
async def get_answer(
    answer_id: int,
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get answer details by ID.
    
    - **answer_id**: Answer ID to retrieve
    
    Returns detailed answer information including permissions for current user.
    """
    answer = db.query(Answer).options(
        joinedload(Answer.author),
        joinedload(Answer.question)
    ).filter(Answer.id == answer_id).first()
    
    if not answer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Answer not found"
        )
    
    # Create detailed response with permissions
    answer_detail = AnswerDetail.model_validate(answer)
    
    if current_user:
        # Check user's vote on this answer
        from ...models.vote import Vote
        user_vote = db.query(Vote).filter(
            Vote.answer_id == answer_id,
            Vote.user_id == current_user.id
        ).first()
        
        if user_vote:
            answer_detail.user_vote = user_vote.is_upvote
        
        # Set permissions
        answer_detail.can_accept = (
            current_user.id == answer.question.author_id or current_user.is_admin
        )
        answer_detail.can_edit = (
            current_user.id == answer.author_id or current_user.is_admin
        )
        answer_detail.can_delete = (
            current_user.id == answer.author_id or current_user.is_admin
        )
    
    return answer_detail


@router.put("/{answer_id}", response_model=AnswerResponse)
async def update_answer(
    answer_id: int,
    answer_update: AnswerUpdate,
    current_user: User = Depends(require_auth),
    permission_checker = Depends(get_permission_checker),
    db: Session = Depends(get_db)
):
    """
    Update an answer.
    
    - **answer_id**: Answer ID to update
    - **content**: Updated content (optional)
    
    Only the answer author or admins can update answers.
    """
    answer = db.query(Answer).filter(Answer.id == answer_id).first()
    
    if not answer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Answer not found"
        )
    
    # Check permissions
    if not permission_checker.can_edit_answer(answer_id, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to edit this answer"
        )
    
    # Update fields
    if answer_update.content is not None:
        answer.content = answer_update.content
    
    db.commit()
    db.refresh(answer)
    
    logger.info(f"Answer updated by {current_user.username}: {answer_id}")
    
    return answer


@router.post("/{answer_id}/accept", response_model=MessageResponse)
async def accept_answer(
    answer_id: int,
    accept_data: AnswerAccept,
    current_user: User = Depends(require_auth),
    permission_checker = Depends(get_permission_checker),
    db: Session = Depends(get_db)
):
    """
    Accept or unaccept an answer.
    
    - **answer_id**: Answer ID to accept/unaccept
    - **is_accepted**: Whether to accept (true) or unaccept (false) the answer
    
    Only the question author or admins can accept answers.
    """
    answer = db.query(Answer).options(joinedload(Answer.question)).filter(
        Answer.id == answer_id
    ).first()
    
    if not answer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Answer not found"
        )
    
    # Check permissions
    if not permission_checker.can_accept_answer(answer_id, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to accept this answer"
        )
    
    question = answer.question
    
    if accept_data.is_accepted:
        # Unaccept any previously accepted answer
        if question.accepted_answer_id:
            old_accepted = db.query(Answer).filter(
                Answer.id == question.accepted_answer_id
            ).first()
            if old_accepted:
                old_accepted.is_accepted = False
        
        # Accept this answer
        answer.is_accepted = True
        question.accepted_answer_id = answer.id
        question.has_accepted_answer = True
        
        message = "Answer accepted successfully"
    else:
        # Unaccept the answer
        answer.is_accepted = False
        question.accepted_answer_id = None
        question.has_accepted_answer = False
        
        message = "Answer unaccepted successfully"
    
    db.commit()
    
    logger.info(f"Answer {answer_id} {'accepted' if accept_data.is_accepted else 'unaccepted'} by {current_user.username}")
    
    return MessageResponse(
        message=message,
        success=True
    )


@router.delete("/{answer_id}", response_model=MessageResponse)
async def delete_answer(
    answer_id: int,
    current_user: User = Depends(require_auth),
    permission_checker = Depends(get_permission_checker),
    db: Session = Depends(get_db)
):
    """
    Delete an answer.
    
    - **answer_id**: Answer ID to delete
    
    Only the answer author or admins can delete answers.
    This will also delete all associated votes and comments.
    """
    answer = db.query(Answer).options(joinedload(Answer.question)).filter(
        Answer.id == answer_id
    ).first()
    
    if not answer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Answer not found"
        )
    
    # Check permissions
    if not permission_checker.can_delete_answer(answer_id, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this answer"
        )
    
    question = answer.question
    
    # If this was the accepted answer, update question
    if answer.is_accepted:
        question.accepted_answer_id = None
        question.has_accepted_answer = False
    
    # Update question answer count
    question.answer_count = max(0, question.answer_count - 1)
    
    # Update user answer count
    answer_author = db.query(User).filter(User.id == answer.author_id).first()
    if answer_author:
        answer_author.answers_count = max(0, answer_author.answers_count - 1)
    
    # Delete answer (cascade will handle related records)
    db.delete(answer)
    db.commit()
    
    logger.info(f"Answer deleted by {current_user.username}: {answer_id}")
    
    return MessageResponse(
        message="Answer deleted successfully",
        success=True
    )
