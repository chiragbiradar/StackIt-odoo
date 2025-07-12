"""
User Service for StackIt Q&A platform.
Handles user profile and statistics operations.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

# Import database dependencies
from database import get_db
from database.models import Answer, Question, User, Vote

# Import schemas
from schemas.user import UserProfile, UserStats

# Create router
router = APIRouter()


@router.get("/{user_id}", response_model=UserProfile)
async def get_user_profile(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get user profile by ID.

    Returns user information including:
    - Basic profile data (username, email, bio, etc.)
    - Statistics (questions count, answers count, reputation)
    - Account status and verification info
    """
    try:
        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Return user profile
        return UserProfile.model_validate(user)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user profile: {str(e)}"
        ) from e


@router.get("/{user_id}/stats", response_model=UserStats)
async def get_user_stats(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed user statistics.

    Returns:
    - Questions count
    - Answers count
    - Reputation score
    - Total votes received on answers
    - Accepted answers count
    """
    try:
        # Check if user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Get questions count
        questions_count = db.query(func.count(Question.id)).filter(
            Question.author_id == user_id
        ).scalar() or 0

        # Get answers count
        answers_count = db.query(func.count(Answer.id)).filter(
            Answer.author_id == user_id
        ).scalar() or 0

        # Get total votes received on user's answers
        votes_received = db.query(func.count(Vote.id)).join(
            Answer, Vote.answer_id == Answer.id
        ).filter(Answer.author_id == user_id).scalar() or 0

        # Get accepted answers count
        accepted_answers = db.query(func.count(Answer.id)).filter(
            Answer.author_id == user_id,
            Answer.is_accepted
        ).scalar() or 0

        return UserStats(
            questions_count=questions_count,
            answers_count=answers_count,
            reputation_score=user.reputation_score,
            votes_received=votes_received,
            accepted_answers=accepted_answers
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user statistics: {str(e)}"
        ) from e


@router.get("/", response_model=list[UserProfile])
async def list_users(
    skip: int = 0,
    limit: int = 20,
    order_by: str = "reputation",
    db: Session = Depends(get_db)
):
    """
    List users with pagination and ordering.

    Query parameters:
    - skip: Number of users to skip (for pagination)
    - limit: Maximum number of users to return (max 100)
    - order_by: Sort order - "reputation", "newest", "oldest", "username"

    Returns list of user profiles with specified ordering.
    """
    try:
        # Limit the maximum number of users that can be requested
        limit = min(limit, 100)

        # Build base query
        query = db.query(User).filter(User.is_active)

        # Apply ordering based on order_by parameter
        if order_by == "reputation":
            query = query.order_by(User.reputation_score.desc(), User.created_at.desc())
        elif order_by == "newest":
            query = query.order_by(User.created_at.desc())
        elif order_by == "oldest":
            query = query.order_by(User.created_at.asc())
        elif order_by == "username":
            query = query.order_by(User.username.asc())
        else:
            # Default to reputation if invalid order_by value
            query = query.order_by(User.reputation_score.desc(), User.created_at.desc())

        # Execute query with pagination
        users = query.offset(skip).limit(limit).all()

        return [UserProfile.model_validate(user) for user in users]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching users: {str(e)}"
        ) from e
