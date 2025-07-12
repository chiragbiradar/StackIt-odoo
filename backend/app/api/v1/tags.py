"""
Tag management API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func
from typing import Optional, List
import logging

from ...database import get_db
from ...models.tag import Tag, QuestionTag
from ...models.user import User
from ...schemas.tag import (
    TagCreate, TagUpdate, TagResponse, TagList, TagUsage, TagSearch
)
from ...schemas.common import (
    PaginationParams, PaginatedResponse, MessageResponse
)
from ...auth.dependencies import require_admin, get_current_active_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=PaginatedResponse[TagList])
async def list_tags(
    pagination: PaginationParams = Depends(),
    search: Optional[str] = Query(None, description="Search tags by name"),
    sort_by: str = Query("usage_count", description="Sort field"),
    order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    min_usage: Optional[int] = Query(None, ge=0, description="Minimum usage count"),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of tags.
    
    - **page**: Page number (default: 1)
    - **size**: Items per page (default: 20, max: 100)
    - **search**: Search term for tag name
    - **sort_by**: Sort field (name, usage_count, created_at)
    - **order**: Sort order (asc, desc)
    - **min_usage**: Minimum usage count filter
    """
    query = db.query(Tag)
    
    # Apply search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(Tag.name.ilike(search_term))
    
    # Apply usage filter
    if min_usage is not None:
        query = query.filter(Tag.usage_count >= min_usage)
    
    # Apply sorting
    sort_column = getattr(Tag, sort_by, Tag.usage_count)
    if order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    tags = query.offset(pagination.offset).limit(pagination.size).all()
    
    return PaginatedResponse.create(
        items=tags,
        total=total,
        page=pagination.page,
        size=pagination.size
    )


@router.get("/popular", response_model=List[TagUsage])
async def get_popular_tags(
    limit: int = Query(20, ge=1, le=100, description="Number of tags to return"),
    db: Session = Depends(get_db)
):
    """
    Get most popular tags by usage count.
    
    - **limit**: Number of tags to return (default: 20, max: 100)
    
    Returns tags ordered by usage count in descending order.
    """
    tags = db.query(Tag).order_by(desc(Tag.usage_count)).limit(limit).all()
    
    tag_usage = []
    for tag in tags:
        # Calculate recent usage (last 30 days) - placeholder for now
        recent_usage = tag.usage_count  # TODO: Implement actual recent usage calculation
        trending_score = recent_usage / max(tag.usage_count, 1)  # Simple trending calculation
        
        tag_usage.append(TagUsage(
            tag=tag,
            usage_count=tag.usage_count,
            recent_usage=recent_usage,
            trending_score=trending_score
        ))
    
    return tag_usage


@router.get("/search", response_model=List[TagResponse])
async def search_tags(
    q: str = Query(min_length=1, max_length=50, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Number of results"),
    db: Session = Depends(get_db)
):
    """
    Search tags by name (for autocomplete/suggestions).
    
    - **q**: Search query
    - **limit**: Maximum number of results (default: 10, max: 50)
    
    Returns tags that match the search query, ordered by usage count.
    """
    search_term = f"%{q}%"
    tags = db.query(Tag).filter(
        Tag.name.ilike(search_term)
    ).order_by(desc(Tag.usage_count)).limit(limit).all()
    
    return tags


@router.post("/", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    tag_data: TagCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Create a new tag (Admin only).
    
    - **name**: Tag name (1-50 characters, lowercase, alphanumeric with hyphens/underscores)
    - **description**: Optional tag description
    - **color**: Optional hex color code
    
    Only administrators can create tags directly.
    Tags are usually created automatically when used in questions.
    """
    # Check if tag already exists
    existing_tag = db.query(Tag).filter(Tag.name == tag_data.name).first()
    
    if existing_tag:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tag already exists"
        )
    
    # Create tag
    tag = Tag(
        name=tag_data.name,
        description=tag_data.description,
        color=tag_data.color,
        usage_count=0
    )
    
    db.add(tag)
    db.commit()
    db.refresh(tag)
    
    logger.info(f"Tag created by admin {current_user.username}: {tag.name}")
    
    return tag


@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag(
    tag_id: int,
    db: Session = Depends(get_db)
):
    """
    Get tag details by ID.
    
    - **tag_id**: Tag ID to retrieve
    """
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    
    return tag


@router.get("/name/{tag_name}", response_model=TagResponse)
async def get_tag_by_name(
    tag_name: str,
    db: Session = Depends(get_db)
):
    """
    Get tag details by name.
    
    - **tag_name**: Tag name to retrieve
    """
    tag = db.query(Tag).filter(Tag.name == tag_name.lower()).first()
    
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    
    return tag


@router.put("/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: int,
    tag_update: TagUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Update a tag (Admin only).
    
    - **tag_id**: Tag ID to update
    - **description**: Updated description (optional)
    - **color**: Updated color (optional)
    
    Only administrators can update tags.
    Tag names cannot be changed to maintain consistency.
    """
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    
    # Update fields
    if tag_update.description is not None:
        tag.description = tag_update.description
    
    if tag_update.color is not None:
        tag.color = tag_update.color
    
    db.commit()
    db.refresh(tag)
    
    logger.info(f"Tag updated by admin {current_user.username}: {tag.name}")
    
    return tag


@router.delete("/{tag_id}", response_model=MessageResponse)
async def delete_tag(
    tag_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Delete a tag (Admin only).
    
    - **tag_id**: Tag ID to delete
    
    Only administrators can delete tags.
    This will remove the tag from all questions that use it.
    """
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    
    tag_name = tag.name
    
    # Delete tag (cascade will handle question_tags relationships)
    db.delete(tag)
    db.commit()
    
    logger.info(f"Tag deleted by admin {current_user.username}: {tag_name}")
    
    return MessageResponse(
        message=f"Tag '{tag_name}' deleted successfully",
        success=True
    )


@router.get("/{tag_id}/questions", response_model=PaginatedResponse)
async def get_tag_questions(
    tag_id: int,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db)
):
    """
    Get questions that use a specific tag.
    
    - **tag_id**: Tag ID to get questions for
    - **page**: Page number (default: 1)
    - **size**: Items per page (default: 20, max: 100)
    """
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    
    # Get questions using this tag
    from ...models.question import Question
    
    query = db.query(Question).join(QuestionTag).filter(
        QuestionTag.tag_id == tag_id
    ).order_by(desc(Question.created_at))
    
    total = query.count()
    questions = query.offset(pagination.offset).limit(pagination.size).all()
    
    return PaginatedResponse.create(
        items=questions,
        total=total,
        page=pagination.page,
        size=pagination.size
    )
