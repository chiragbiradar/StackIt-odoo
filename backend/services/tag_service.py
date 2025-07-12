"""
Tag Service for StackIt Q&A platform.
Handles tag listing and management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

# Import database dependencies
from database import get_db
from database.models import Tag

# Import schemas
from schemas.tag import TagListResponse, TagResponse

# Create router
router = APIRouter()


@router.get("/tags", response_model=TagListResponse)
async def list_tags(
    db: Session = Depends(get_db)
):
    """
    List all available tags ordered by usage count.

    Returns tags with their usage statistics for question creation forms.
    """
    try:
        # Get all tags ordered by usage count (most used first)
        tags = db.query(Tag).order_by(desc(Tag.usage_count)).all()

        # Build response
        tag_responses = [
            TagResponse(
                id=tag.id,
                name=tag.name,
                description=tag.description,
                color=tag.color,
                usage_count=tag.usage_count
            )
            for tag in tags
        ]

        return TagListResponse(
            tags=tag_responses,
            total=len(tag_responses)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching tags: {str(e)}"
        ) from e
