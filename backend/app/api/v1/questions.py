"""
Question management API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, asc, func, or_
from typing import Optional, List
import logging

from ...database import get_db
from ...models.question import Question
from ...models.tag import Tag, QuestionTag
from ...models.user import User
from ...schemas.question import (
    QuestionCreate, QuestionUpdate, QuestionResponse, QuestionList,
    QuestionDetail, QuestionSearch
)
from ...schemas.common import (
    PaginationParams, PaginatedResponse, MessageResponse
)
from ...auth.dependencies import (
    get_current_active_user, require_auth, get_permission_checker
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=PaginatedResponse[QuestionList])
async def list_questions(
    pagination: PaginationParams = Depends(),
    search: Optional[str] = Query(None, description="Search questions by title or content"),
    tags: Optional[List[str]] = Query(None, description="Filter by tag names"),
    author_id: Optional[int] = Query(None, description="Filter by author ID"),
    has_accepted_answer: Optional[bool] = Query(None, description="Filter by accepted answer status"),
    is_closed: Optional[bool] = Query(None, description="Filter by closed status"),
    sort_by: str = Query("created_at", description="Sort field"),
    order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of questions.
    
    - **page**: Page number (default: 1)
    - **size**: Items per page (default: 20, max: 100)
    - **search**: Search term for title or description
    - **tags**: Filter by tag names (can specify multiple)
    - **author_id**: Filter by question author
    - **has_accepted_answer**: Filter by accepted answer status
    - **is_closed**: Filter by closed status
    - **sort_by**: Sort field (created_at, vote_score, view_count, answer_count)
    - **order**: Sort order (asc, desc)
    """
    query = db.query(Question).options(
        joinedload(Question.author),
        joinedload(Question.question_tags).joinedload(QuestionTag.tag)
    )
    
    # Apply search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Question.title.ilike(search_term),
                Question.description.ilike(search_term)
            )
        )
    
    # Apply tag filter
    if tags:
        tag_ids = db.query(Tag.id).filter(Tag.name.in_(tags)).subquery()
        question_ids = db.query(QuestionTag.question_id).filter(
            QuestionTag.tag_id.in_(tag_ids)
        ).subquery()
        query = query.filter(Question.id.in_(question_ids))
    
    # Apply other filters
    if author_id:
        query = query.filter(Question.author_id == author_id)
    
    if has_accepted_answer is not None:
        query = query.filter(Question.has_accepted_answer == has_accepted_answer)
    
    if is_closed is not None:
        query = query.filter(Question.is_closed == is_closed)
    
    # Apply sorting
    sort_column = getattr(Question, sort_by, Question.created_at)
    if order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    questions = query.offset(pagination.offset).limit(pagination.size).all()
    
    return PaginatedResponse.create(
        items=questions,
        total=total,
        page=pagination.page,
        size=pagination.size
    )


@router.post("/", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
async def create_question(
    question_data: QuestionCreate,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Create a new question.
    
    - **title**: Question title (10-200 characters)
    - **description**: Question description in rich text (minimum 20 characters)
    - **tag_names**: List of tag names (1-5 tags)
    
    Requires authentication and email verification.
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required to ask questions"
        )
    
    # Create question
    question = Question(
        title=question_data.title,
        description=question_data.description,
        author_id=current_user.id
    )
    
    db.add(question)
    db.flush()  # Get question ID
    
    # Handle tags
    for tag_name in question_data.tag_names:
        # Get or create tag
        tag = db.query(Tag).filter(Tag.name == tag_name).first()
        if not tag:
            tag = Tag(name=tag_name, usage_count=0)
            db.add(tag)
            db.flush()
        
        # Create question-tag relationship
        question_tag = QuestionTag(question_id=question.id, tag_id=tag.id)
        db.add(question_tag)
        
        # Update tag usage count
        tag.usage_count += 1
    
    # Update user question count
    current_user.questions_count += 1
    
    db.commit()
    db.refresh(question)
    
    logger.info(f"Question created by {current_user.username}: {question.title}")
    
    return question


@router.get("/{question_id}", response_model=QuestionDetail)
async def get_question(
    question_id: int,
    db: Session = Depends(get_db)
):
    """
    Get question details by ID.
    
    - **question_id**: Question ID to retrieve
    
    Returns detailed question information including author and tags.
    Also increments the view count.
    """
    question = db.query(Question).options(
        joinedload(Question.author),
        joinedload(Question.question_tags).joinedload(QuestionTag.tag)
    ).filter(Question.id == question_id).first()
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    # Increment view count
    question.view_count += 1
    db.commit()
    
    return question


@router.put("/{question_id}", response_model=QuestionResponse)
async def update_question(
    question_id: int,
    question_update: QuestionUpdate,
    current_user: User = Depends(require_auth),
    permission_checker = Depends(get_permission_checker),
    db: Session = Depends(get_db)
):
    """
    Update a question.
    
    - **question_id**: Question ID to update
    - **title**: Updated title (optional)
    - **description**: Updated description (optional)
    - **tag_names**: Updated tag names (optional)
    - **is_closed**: Close/open question (optional)
    
    Only the question author or admins can update questions.
    """
    question = db.query(Question).filter(Question.id == question_id).first()
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    # Check permissions
    if not permission_checker.can_edit_question(question_id, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to edit this question"
        )
    
    # Update fields
    if question_update.title is not None:
        question.title = question_update.title
    
    if question_update.description is not None:
        question.description = question_update.description
    
    if question_update.is_closed is not None:
        question.is_closed = question_update.is_closed
    
    # Update tags if provided
    if question_update.tag_names is not None:
        # Remove existing tags
        db.query(QuestionTag).filter(QuestionTag.question_id == question_id).delete()
        
        # Add new tags
        for tag_name in question_update.tag_names:
            tag = db.query(Tag).filter(Tag.name == tag_name).first()
            if not tag:
                tag = Tag(name=tag_name, usage_count=0)
                db.add(tag)
                db.flush()
            
            question_tag = QuestionTag(question_id=question.id, tag_id=tag.id)
            db.add(question_tag)
            tag.usage_count += 1
    
    db.commit()
    db.refresh(question)
    
    logger.info(f"Question updated by {current_user.username}: {question.title}")
    
    return question


@router.delete("/{question_id}", response_model=MessageResponse)
async def delete_question(
    question_id: int,
    current_user: User = Depends(require_auth),
    permission_checker = Depends(get_permission_checker),
    db: Session = Depends(get_db)
):
    """
    Delete a question.
    
    - **question_id**: Question ID to delete
    
    Only the question author or admins can delete questions.
    This will also delete all associated answers, votes, and comments.
    """
    question = db.query(Question).filter(Question.id == question_id).first()
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    # Check permissions
    if not permission_checker.can_delete_question(question_id, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this question"
        )
    
    question_title = question.title
    
    # Delete question (cascade will handle related records)
    db.delete(question)
    
    # Update user question count
    question_author = db.query(User).filter(User.id == question.author_id).first()
    if question_author:
        question_author.questions_count = max(0, question_author.questions_count - 1)
    
    db.commit()
    
    logger.info(f"Question deleted by {current_user.username}: {question_title}")
    
    return MessageResponse(
        message="Question deleted successfully",
        success=True
    )
