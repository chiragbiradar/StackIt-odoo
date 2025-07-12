"""
Example Service - Template for creating other services
This shows the structure for creating API routes in the services folder.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

# Import database dependencies
from database import get_db
from database.models import User

# Import schemas (will be created)
# from schemas.user import UserCreate, UserResponse

# Create router
router = APIRouter()

# Example endpoint structure
@router.get("/")
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all users with pagination.
    This is an example of how to structure service endpoints.
    """
    try:
        users = db.query(User).offset(skip).limit(limit).all()
        return {
            "users": users,
            "total": len(users),
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching users: {str(e)}"
        )


@router.get("/{user_id}")
async def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific user by ID.
    Example of single resource endpoint.
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user: {str(e)}"
        )


# Example of how to include this router in server.py:
# from services.example_service import router as example_router
# app.include_router(example_router, prefix="/api/v1/users", tags=["Users"])

"""
To create a new service:

1. Copy this file and rename it (e.g., auth_service.py)
2. Update the imports to match your needs
3. Create the corresponding schemas in schemas/ folder
4. Implement your business logic
5. Add the router to server.py

Example service files to create:
- auth_service.py (login, register, logout)
- question_service.py (CRUD for questions)
- answer_service.py (CRUD for answers)
- user_service.py (user profile management)
- tag_service.py (tag management)
- vote_service.py (voting system)
- notification_service.py (notifications)
"""
