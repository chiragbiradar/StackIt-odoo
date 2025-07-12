"""
User Service for StackIt Q&A platform.
Handles user profile retrieval.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

# Import database dependencies
from database import get_db
from database.models import User

# Import schemas
from schemas.user import UserProfile

# Create router
router = APIRouter()


@router.get("/users/{user_id}", response_model=UserProfile)
async def get_user_profile(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get user profile by ID.
    
    - **user_id**: ID of the user to retrieve
    
    Returns user information including statistics like questions and answers count.
    """
    try:
        # Get user by ID
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserProfile(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            bio=user.bio,
            avatar_url=user.avatar_url,
            is_active=user.is_active,
            is_verified=user.is_verified,
            role=user.role.value,  # Convert enum to string
            reputation_score=user.reputation_score,
            questions_count=user.questions_count,
            answers_count=user.answers_count,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user profile: {str(e)}"
        ) from e
